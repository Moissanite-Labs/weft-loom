"""tf_step6.py : attention graft for REVERSE (task 3) into a host that knows COPY and ADD3.

Host: 2-layer decoder as in tf_seeds.py, trained on COPY+ADD3 (same seeds, so same hosts as tf_seeds.py std mode).
Donor: same shape, other init, trained on COPY+ADD3+REVERSE 1400 steps (as in committed script, task 2 replaced by 3).
Design (all choices mine):
  Graft  = one attention head (q,k,v: 128->32 with bias; o: 32->128, no bias) = 16,480 parameters = 32,960 bytes fp16,
           reading the same LN1 input as the host heads of its block, output added to that block's attention output.
  mode add  : extra 5th head (needs added width in the host, cannot be written into existing d_model=128 weights).
  mode rep  : repurpose host head h* of the same block (h* = head whose ablation changes native outputs least,
              measured per seed); the head's q,k,v rows and its o columns are OVERWRITTEN, nothing is added.
  Loss per step = KL(student || donor) on REVERSE batches + KL(student || frozen host) on COPY/ADD3 batches
  (preservation term; no true labels anywhere). Everything in the host is frozen; only the graft (and packet) trains.
  Eval: teacher-forced argmax accuracy at positions 7..12, 512 examples per task, fresh draws (std) and held-out tuples.
Controls (--set controls): ctl_mlp_only_r64_blk2/blk1 (no attention graft; a position-wise packet of hidden width 64 =
  16,576 parameters at the block-2 / block-1 MLP boundary, same loss), nopres (no
  preservation term, add_L1), hide (add_L1; context token replaced by neutral token 0 in student inputs, targets from real inputs;
  evaluated with the real token and with the token hidden).
The script exits non-zero on internal inconsistency (functional forward mismatch, written model != graft model, a frozen
host parameter changed).
"""
import argparse
import json
import sys
import time

from tf_attn import *  # noqa

STEPS = 8000
SEED_DEFAULT = list(range(3, 11))


def make_sets(seed):
    ge = torch.Generator().manual_seed(7000 + seed)
    ins = {t: batch([t], 512, ge) for t in (0, 1, 2, 3)}
    ho = {t: batch([t], 512, ge, "test") for t in (0, 1, 2, 3)}
    return {"in": ins, "ho": ho}


def head_ablation(host, nat_x, nat_y, ref_logits):
    """per (block, head): native acc with that head zeroed and mean KL(ref||ablated) on native positions."""
    out = {}
    for bi in (1, 2):
        for h in range(H):
            with torch.no_grad():
                lg = fwd(host, nat_x, ablate={bi: [h]})
                a = float(((lg[:, 7:13].argmax(-1)) == nat_y[:, 8:14]).float().mean())
                kl = float(kl_loss(lg, ref_logits, nat_y))
            out[f"b{bi}h{h}"] = {"native_acc": round(a, 4), "kl": kl}
        with torch.no_grad():
            lg = fwd(host, nat_x, ablate={bi: list(range(H))})
            out[f"b{bi}_all_heads"] = {"native_acc": round(float(((lg[:, 7:13].argmax(-1)) == nat_y[:, 8:14]).float().mean()), 4),
                                       "kl": float(kl_loss(lg, ref_logits, nat_y))}
    return out


def dormant_slots(host, g):
    host.eval()
    with torch.no_grad():
        acts = []
        for _ in range(8):
            x, _ = batch([0, 1], 64, g)
            mask = torch.full((L, L), float("-inf")).triu(1)
            h = host.emb(x) + host.pos(torch.arange(L))
            h = host.b1(h, mask)
            b = host.b2
            hh = b.ln1(h)
            a, _ = b.attn(hh, hh, hh, attn_mask=mask, need_weights=False)
            h = h + a
            acts.append(F.gelu(b.up(b.ln2(h))).pow(2).mean(dim=(0, 1)))
        fisher = torch.stack(acts).mean(0) * host.b2.down.weight.pow(2).sum(0)
    return torch.argsort(fisher)[:32]


def write_all(host, graft, layer, hstar, packet, slots):
    m = copy.deepcopy(host)
    if graft is not None:
        graft.write_into(m.b1 if layer == 1 else m.b2, hstar)
    if packet is not None:
        b = m.b2
        r = packet.l1.weight.shape[0]
        with torch.no_grad():
            b.up.weight[slots[:r]] = packet.l1.weight
            b.up.bias[slots[:r]] = packet.l1.bias
            b.down.weight[:, slots[:r]] = packet.l2.weight
            b.down.bias += packet.l2.bias
    return m


def train_variant(host, donor, cfg, seed, ev, slots, nat_ref_params=None):
    """cfg: layer, mode(add|rep|none), hstar, r(packet width, 0 none), preserve, hide, steps, lr"""
    torch.manual_seed(500 + seed)
    gg = torch.Generator().manual_seed(8000 + seed)
    graft = Graft() if cfg["mode"] != "none" else None
    packet = Packet(cfg["r"]) if cfg["r"] > 0 else None
    params = (list(graft.parameters()) if graft else []) + (list(packet.parameters()) if packet else [])
    n_train = sum(p.numel() for p in params)
    opt = torch.optim.AdamW(params, lr=cfg["lr"])
    abl = {cfg["layer"]: [cfg["hstar"]]} if cfg["mode"] == "rep" else None
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, cfg["steps"])
    curve = []

    def student(x, hide=False):
        xs = x.clone()
        if hide:
            xs[:, 0] = 0
        return fwd(host, xs, graft=graft, graft_block=cfg["layer"], ablate=abl, packet=packet, packet_block=cfg.get("pk_block", 2))

    def ev_now(hide=False):
        r = {}
        with torch.no_grad():
            for t, (x, y) in ev["in"].items():
                if t == 2:
                    continue
                xs = x.clone()
                if hide:
                    xs[:, 0] = 0
                r[t] = round(float((student(x, hide)[:, 7:13].argmax(-1) == y[:, 8:14]).float().mean()), 4)
        return r

    for step in range(cfg["steps"] + 1):
        if step % 250 == 0:
            curve.append((step, ev_now(cfg.get("hide_eval", False))))
        if step == cfg["steps"]:
            break
        loss = 0.0
        x, y = batch([3], 64, gg)
        with torch.no_grad():
            tl = donor(x)
        loss = loss + kl_loss(student(x, cfg["hide"]), tl, y)
        if cfg["preserve"]:
            x, y = batch([0, 1], 64, gg)
            with torch.no_grad():
                tl = fwd(host, x)
            loss = loss + kl_loss(student(x, cfg["hide"]), tl, y)
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    return graft, packet, curve, n_train


def run(seed, cfgs, tag_filter=None):
    t0 = time.time()
    import os
    cp = f"cache/hd_{seed}.pt"
    if os.path.exists(cp):
        host, donor = TF(), TF()
        sd = torch.load(cp)
        host.load_state_dict(sd["host"]); donor.load_state_dict(sd["donor"])
    else:
        torch.manual_seed(100 + seed)
        g = torch.Generator().manual_seed(1000 + seed)
        host = train(TF(), [0, 1], 1200, g)
        torch.manual_seed(200 + seed)
        donor = train(TF(), [0, 1, 3], 1400, g)
        os.makedirs("cache", exist_ok=True)
        torch.save({"host": host.state_dict(), "donor": donor.state_dict()}, cp)
    for p in list(host.parameters()) + list(donor.parameters()):
        p.requires_grad_(False)
    host_orig = {k: p.detach().clone() for k, p in host.named_parameters()}
    ev = make_sets(seed)
    parity_check(host, ev["in"][3][0])
    out = {"seed": seed, "host": {n: acc_on(host, S) for n, S in ev.items()},
           "donor": {n: acc_on(donor, S) for n, S in ev.items()}}
    nx = torch.cat([ev["in"][0][0][:256], ev["in"][1][0][:256]])
    ny = torch.cat([ev["in"][0][1][:256], ev["in"][1][1][:256]])
    with torch.no_grad():
        ref = host(nx)
    out["head_ablation"] = head_ablation(host, nx, ny, ref)
    hstar = {}
    for bi in (1, 2):
        hstar[bi] = min(range(H), key=lambda h: out["head_ablation"][f"b{bi}h{h}"]["kl"])
    out["hstar"] = hstar
    slots = dormant_slots(host, torch.Generator().manual_seed(9000 + seed))
    out["variants"] = {}
    for name, cfg in cfgs.items():
        if tag_filter and name not in tag_filter:
            continue
        cfg = dict(cfg)
        cfg["hstar"] = hstar[cfg["layer"]]
        graft, packet, curve, n_train = train_variant(host, donor, cfg, seed, ev, slots)
        v = {"cfg": {k: val for k, val in cfg.items()}, "n_trainable": n_train,
             "graft_bytes_fp16": n_train * 2, "curve": curve}
        # evaluation on real inputs
        kw = dict(graft=graft, graft_block=cfg["layer"], ablate=({cfg["layer"]: [cfg["hstar"]]} if cfg["mode"] == "rep" else None), packet=packet, packet_block=cfg.get("pk_block", 2))
        v["external"] = {n: acc_f(host, S, **kw) for n, S in ev.items()}
        with torch.no_grad():
            xr, yr = ev["in"][3]
            pr = fwd(host, xr, **kw)[:, 7:13].argmax(-1)
            v["rev_pos_acc"] = [round(float((pr[:, i] == yr[:, 8 + i]).float().mean()), 3) for i in range(6)]
        if cfg["hide"]:
            hid = {n: {t: (torch.cat([x[:, :1] * 0, x[:, 1:]], 1), y) for t, (x, y) in S.items()} for n, S in ev.items()}
            v["external_hidden"] = {n: acc_f(host, S, **kw) for n, S in hid.items()}
        if cfg["mode"] == "rep":
            m = write_all(host, graft, cfg["layer"], cfg["hstar"], packet, slots)
            v["written"] = {n: acc_on(m, S) for n, S in ev.items()}
            with torch.no_grad():
                xb = ev["in"][3][0]
                if packet is None:
                    d = float((m(xb) - fwd(host, xb, **kw)).abs().max())
                    if d > 1e-3:
                        die("written model differs from graft model by %g" % d)
                    v["max_logit_diff_written_vs_graft"] = d
                else:
                    v["max_logit_diff_written_vs_graft"] = float((m(xb) - fwd(host, xb, **kw)).abs().max())
            v["frob_dist"] = frob_dist(m, host)
            v["gate10"] = v["frob_dist"] <= 10.0
            v["gate120"] = v["frob_dist"] <= 120.0
        for k, p in host.named_parameters():
            if not torch.equal(p.detach(), host_orig[k]):
                die("host parameter changed: " + k)
        out["variants"][name] = v
        print(json.dumps({"seed": seed, "variant": name, "ext_in": v["external"]["in"], "written_in": v.get("written", {}).get("in"),
                          "ho": v["external"]["ho"], "hidden": v.get("external_hidden", {}).get("in")}), flush=True)
    out["secs"] = round(time.time() - t0, 1)
    return out


MAIN = {
    "add_L1": dict(layer=1, mode="add", r=0, preserve=True, hide=False, steps=STEPS, lr=3e-3),
    "rep_L1": dict(layer=1, mode="rep", r=0, preserve=True, hide=False, steps=STEPS, lr=3e-3),
    "add_L2": dict(layer=2, mode="add", r=0, preserve=True, hide=False, steps=STEPS, lr=3e-3),
    "rep_L2": dict(layer=2, mode="rep", r=0, preserve=True, hide=False, steps=STEPS, lr=3e-3),
}
CONTROLS = {
    "ctl_mlp_only_r64_blk2": dict(layer=2, mode="none", r=64, pk_block=2, preserve=True, hide=False, steps=STEPS, lr=3e-3),
    "ctl_mlp_only_r64_blk1": dict(layer=1, mode="none", r=64, pk_block=1, preserve=True, hide=False, steps=STEPS, lr=3e-3),
    "ctl_nopres_add_L1": dict(layer=1, mode="add", r=0, preserve=False, hide=False, steps=STEPS, lr=3e-3),
    "ctl_nopres_rep_L2": dict(layer=2, mode="rep", r=0, preserve=False, hide=False, steps=STEPS, lr=3e-3),
    "ctl_hide_rep_L2": dict(layer=2, mode="rep", r=0, preserve=True, hide=True, steps=STEPS, lr=3e-3),
    "ctl_hide_add_L1": dict(layer=1, mode="add", r=0, preserve=True, hide=True, steps=STEPS, lr=3e-3),
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=SEED_DEFAULT)
    ap.add_argument("--set", default="main", choices=["main", "controls"])
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--steps", type=int)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cfgs = MAIN if a.set == "main" else CONTROLS
    if a.steps:
        cfgs = {k: dict(v, steps=a.steps) for k, v in cfgs.items()}
    res = []
    for s in a.seeds:
        res.append(run(s, cfgs, a.only))
        json.dump(res, open(a.out, "w"), indent=1)

# Design history (honest): graft optimisation was explored on seed 3 only (STEPS 2500 -> 8000, lr 3e-3 cosine; lr 1e-2 and 3e-2
# tried in explore_graft.py). The 8000-step config was fixed after seeing seed 3, so seed 3 is not a clean test; seeds 4..10 are.
