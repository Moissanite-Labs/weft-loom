"""tf_seeds.py : fresh-seed replication and controls for the committed transformer splice result
(probes/tf_splice3.py, 272,384-parameter 2-layer decoder, MUL5 skill spliced into 32 dormant MLP neurons).

PASS BAR, exactly as the committed script defines it (tf_splice3.py, last lines):
    a seed passes when
        spliced[task 2 acc] >= donor_acc_on_task2 - 0.10
        AND host_acc[COPY]  - spliced_acc[COPY]  <= 0.02
        AND host_acc[ADD3]  - spliced_acc[ADD3]  <= 0.02
    "spliced" = host with the packet written into the 32 lowest-Fisher up/down neurons of the last MLP.
    donor_acc is the donor's task-2 accuracy; host_acc is the unmodified host on the same eval set.
    Accuracy = argmax at positions 7..12 vs target tokens 8..13, teacher forced, 512 examples per task.
  Here the same bar is applied to every arm (host/donor accuracies come from the same test set as the arm).
  Notes on the committed script: its docstring still says REVERSE and its JSON field "bar" says "2/3"
  while the printed bar line says 2/2; the code run is MUL5 (task 2 = y = 5 + 5*(x-5) mod 16) and 2 seeds.

SEEDS. Committed: splice.py (reverse) 0,1,2; splice2.py 0,1; splice3.py 0,1.
  Fresh (this file): 3..22 (20 seeds). Seed s uses torch seeds 100+s, 200+s, generators 1000+s, 9000+s
  (as committed); extra arms use 300+s, 5000+s, 6000+s, 7000+s, none of which collide with 0,1,2.
  --check-committed runs seeds 0,1 in committed-order and compares to the committed JSON exactly.

MODES. std: samplers exactly as committed. ho: all training (host, donor, packets) excludes operand tuples whose six
  values sum to a multiple of 7; the held-out test set contains only such tuples. Test sets are reported for both.
  Position-wise skills see all 16 token values in training either way: held-out here means unseen operand
  combinations, not unseen token values. Sequence length is fixed at 6 operands (no length hold-out is possible
  with learned positional embeddings of fixed L=14).

ARMS (each on every seed):
  host                     unmodified host
  pres_true_{ext,dorm,rand,topF}   committed packet (CE on true labels, task 2 + native CE through frozen host);
                           ext = external residual adapter, dorm = spliced into dormant slots (committed),
                           rand = same packet written into 32 random slots, topF = into the 32 highest-Fisher slots
  pres_donor_{ext,dorm,rand}  packet trained to match the DONOR logits (KL, no true labels) on task-2 batches and on
                           native batches (preservation term, target = donor's native outputs)
  plain_true_{ext,dorm}    packet trained on task 2 only, true labels (committed splice2)
  plain_donor_{ext,dorm}   same, KL to donor
  router                   host with plain_true packet applied only when task token == 3 (external, no splice)
"""
import argparse
import json
import sys
import time

import torch

from tf_common import *  # noqa

COMMITTED = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "weft-threads-2026-11-15", "probes", "tf-splice3-results.json")


def passes(a, host, donor):
    return bool(a[2] >= donor[2] - 0.10 and host[0] - a[0] <= 0.02 and host[1] - a[1] <= 0.02)


def splice(host, packet, slots):
    sp = copy.deepcopy(host)
    with torch.no_grad():
        b = sp.b2
        b.up.weight[slots] = packet.l1.weight
        b.up.bias[slots] = packet.l1.bias
        b.down.weight[:, slots] = packet.l2.weight
        b.down.bias += packet.l2.bias
    return sp


def fit_packet(host, donor, packet, kind, g, split, rec):
    """kind: pres_true | pres_donor | plain_true | plain_donor"""
    if kind == "plain_true":
        train(host, [2], 800, g, packet=packet, lr=3e-3, split=split, rec=rec)
        return
    steps, lr = (900, 3e-3) if kind.startswith("pres") else (800, 3e-3)
    opt = torch.optim.AdamW(packet.parameters(), lr=lr)
    host.train()
    for _ in range(steps):
        loss = 0.0
        groups = [[2], [0, 1]] if kind.startswith("pres") else [[2]]
        for tasks_ in groups:
            x, y = batch(tasks_, 64, g, split, rec)
            logits = host(x, packet=packet)
            if kind.endswith("true"):
                loss = loss + ce_loss(logits, x, y)
            else:
                with torch.no_grad():
                    tl = donor(x)
                loss = loss + kl_loss(logits, tl, y)
        opt.zero_grad(); loss.backward(); opt.step()


def run_seed(seed, mode, check_committed=None):
    t0 = time.time()
    split = "any" if mode == "std" else "train"
    rec = set()
    torch.manual_seed(100 + seed)
    g = torch.Generator().manual_seed(1000 + seed)
    host = train(TF(), [0, 1], 1200, g, split=split, rec=rec)
    torch.manual_seed(200 + seed)
    donor = train(TF(), [0, 1, 2], 1400, g, split=split, rec=rec)
    ge = torch.Generator().manual_seed(9000 + seed)
    base_c = acc(host, [0, 1, 2], ge)
    dref_c = acc(donor, [2], ge)[2]

    packet = Packet()
    for p in host.parameters():
        p.requires_grad_(False)
    for p in donor.parameters():
        p.requires_grad_(False)
    fit_packet(host, donor, packet, "pres_true", g, split, rec)  # committed arm, committed RNG order
    ext_c = acc(host, [0, 1, 2], ge, packet=packet)

    host.eval()
    with torch.no_grad():
        acts = []
        for _ in range(8):
            x, _ = batch([0, 1], 64, ge, split)
            mask = torch.full((L, L), float("-inf")).triu(1)
            h = host.emb(x) + host.pos(torch.arange(L))
            h = host.b1(h, mask)
            b = host.b2
            hh = b.ln1(h)
            a, _ = b.attn(hh, hh, hh, attn_mask=mask, need_weights=False)
            h = h + a
            acts.append(F.gelu(b.up(b.ln2(h))).pow(2).mean(dim=(0, 1)))
        fisher = torch.stack(acts).mean(0) * host.b2.down.weight.pow(2).sum(0)
        dorm = torch.argsort(fisher)[:32]
        topF = torch.argsort(fisher, descending=True)[:32]
    spl_c = acc(splice(host, packet, dorm), [0, 1, 2], ge)
    res_committed_style = {"seed": seed, "params": sum(p.numel() for p in host.parameters()),
                           "wire_bytes_fp16": sum(p.numel() for p in packet.parameters()) * 2,
                           "donor_rev": dref_c, "host": base_c, "external": ext_c, "spliced": spl_c,
                           "native_drop": round(min(base_c[0] - spl_c[0], base_c[1] - spl_c[1]) * -1, 4)}
    if res_committed_style["params"] != 272384 or res_committed_style["wire_bytes_fp16"] != 16704:
        die("param or wire byte count differs from the record")
    if check_committed is not None:
        c = check_committed
        for k in ("params", "wire_bytes_fp16", "donor_rev", "host", "external", "spliced", "native_drop"):
            cv = {kk: vv for kk, vv in c[k].items()} if isinstance(c[k], dict) else c[k]
            mv = {str(kk): vv for kk, vv in res_committed_style[k].items()} if isinstance(c[k], dict) else res_committed_style[k]
            if cv != mv:
                die(f"committed mismatch seed {seed} field {k}: {cv} vs {mv}")

    # fixed test sets (independent of the committed-order generator)
    ge2 = torch.Generator().manual_seed(7000 + seed)
    in_split = "any" if mode == "std" else "train"
    SETS = {"in": {t: batch([t], 512, ge2, in_split) for t in (0, 1, 2)},
            "ho": {t: batch([t], 512, ge2, "test") for t in (0, 1, 2)}}
    trainkeys = rec
    overlap = {}
    for name, S in SETS.items():
        ks = set()
        for t, (x, y) in S.items():
            for row in x[:, 1:7]:
                ks.add(key_of((row - 5).tolist()))
            for row in x[:, 1:7]:
                if name == "ho" and not is_heldout((row - 5).tolist()):
                    die("held-out set contains non-held-out tuple")
        overlap[name] = {"n_unique_test_tuples": len(ks), "n_in_training_stream": len(ks & trainkeys)}
    if mode == "ho":
        if any(is_heldout([(k >> (4 * i)) & 15 for i in range(6)]) for k in trainkeys):
            die("held-out tuple found in training stream")
        if overlap["ho"]["n_in_training_stream"] != 0:
            die("held-out test tuples overlap training")

    def ev(model, packet_=None, gate_fn=None):
        return {n: acc_on(model, S, packet=packet_, gate_fn=gate_fn) for n, S in SETS.items()}

    host_ev = ev(host)
    donor_ev = {n: acc_on(donor, {2: S[2]}) for n, S in SETS.items()}
    donor_full = {n: acc_on(donor, S) for n, S in SETS.items()}
    arms = {"host": {"acc": host_ev}}

    def add_arm(name, model, packet_=None, gate_fn=None, spliced=False):
        e = ev(model, packet_, gate_fn)
        r = {"acc": e}
        for n in e:
            r["pass_" + n] = passes(e[n], host_ev[n], {2: donor_ev[n][2]})
        if spliced:
            d = frob_dist(model, host)
            r["frob_dist"] = d
            r["gate10"] = d <= 10.0
            r["gate120"] = d <= 120.0
        arms[name] = r

    torch.manual_seed(300 + seed)
    g2 = torch.Generator().manual_seed(5000 + seed)
    rg = torch.Generator().manual_seed(6000 + seed)
    rand = torch.randperm(FF, generator=rg)[:32]
    if len(set(dorm.tolist()) & set(rand.tolist())) > 32:
        die("slot sets")

    # committed packet in all placements
    add_arm("pres_true_ext", host, packet)
    add_arm("pres_true_dorm", splice(host, packet, dorm), spliced=True)
    add_arm("pres_true_rand", splice(host, packet, rand), spliced=True)
    add_arm("pres_true_topF", splice(host, packet, topF), spliced=True)
    # logit distance between external and dorm-spliced (how exact is "match exactly")
    with torch.no_grad():
        xb, _ = SETS["in"][2]
        d_logit = float((host(xb, packet=packet) - splice(host, packet, dorm)(xb)).abs().max())
    arms["pres_true_dorm"]["max_abs_logit_diff_vs_external"] = d_logit

    pk = {}
    for kind in ("pres_donor", "plain_true", "plain_donor"):
        pk[kind] = Packet()
        fit_packet(host, donor, pk[kind], kind, g2, split, None)
        add_arm(kind + "_ext", host, pk[kind])
        add_arm(kind + "_dorm", splice(host, pk[kind], dorm), spliced=True)
    add_arm("pres_donor_rand", splice(host, pk["pres_donor"], rand), spliced=True)
    add_arm("plain_true_rand", splice(host, pk["plain_true"], rand), spliced=True)
    add_arm("router", host, pk["plain_true"], gate_fn=lambda x: (x[:, 0] == 3).float().view(-1, 1, 1))

    out = {"seed": seed, "mode": mode, "committed_style": res_committed_style,
           "donor_task2": donor_ev, "donor_all": donor_full, "overlap": overlap,
           "arms": arms, "secs": round(time.time() - t0, 1)}
    print(json.dumps(out), flush=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="std", choices=["std", "ho"])
    ap.add_argument("--seeds", type=int, nargs="+", default=list(range(3, 23)))
    ap.add_argument("--check-committed", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    committed = {r["seed"]: r for r in json.load(open(COMMITTED))["seeds"]}
    res = []
    for s in a.seeds:
        if a.check_committed and s not in committed:
            die("no committed record for seed %d" % s)
        res.append(run_seed(s, a.mode, committed[s] if a.check_committed else None))
        json.dump(res, open(a.out, "w"), indent=1)
    if a.check_committed:
        print("committed replication: exact match on seeds", a.seeds)
