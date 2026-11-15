"""tf_step5b.py : follow-up to tf_step5.py. tf_step5 found that REVERSE is learnable with attention frozen
(position-wise MLP + readout training). This asks how small the position-wise change can be and where the
cross-position information comes from.
(1) ladder: attention frozen; trainable group, CE on REVERSE true labels, 2000 steps lr 3e-3:
      readout (final LN + head), mlp2 (block-2 MLP+ln2 + readout), mlp1 (block-1 MLP+ln2 only), and
      external packets of hidden width r in {32, 128, 512, 2048} at the block-2 MLP boundary (tf_common.Packet).
(2) attention diagnostic on REVERSE inputs for the unmodified host: for each head, mean attention mass that
    query position p=7+i puts on the mirror source position 6-i (what REVERSE needs), on the COPY source position 1+i,
    and on position 0, averaged over i and examples.
Exits non-zero if a frozen parameter changed.
"""
import argparse
import json
import time

from tf_attn import *  # noqa

STEPS = 2000


def run(seed):
    t0 = time.time()
    torch.manual_seed(100 + seed)
    g = torch.Generator().manual_seed(1000 + seed)
    host = train(TF(), [0, 1], 1200, g)
    for p in host.parameters():
        p.requires_grad_(False)
    ge = torch.Generator().manual_seed(7000 + seed)
    ev = {t: batch([t], 512, ge) for t in (0, 1, 2, 3)}
    out = {"seed": seed, "host": acc_on(host, ev), "ladder": {}}
    ps = dict(host.named_parameters())
    sel = {
        "readout": [k for k in ps if k.startswith("lnf") or k.startswith("head")],
        "mlp2": [k for k in ps if k.startswith("b2.up") or k.startswith("b2.down") or k.startswith("b2.ln2") or k.startswith("lnf") or k.startswith("head")],
        "mlp1": [k for k in ps if k.startswith("b1.up") or k.startswith("b1.down") or k.startswith("b1.ln2")],
    }
    for name, keys in sel.items():
        m = copy.deepcopy(host)
        orig = {k: p.detach().clone() for k, p in host.named_parameters()}
        tr = []
        for k, p in m.named_parameters():
            p.requires_grad_(k in keys)
            if k in keys:
                tr.append(p)
        opt = torch.optim.AdamW(tr, lr=3e-3)
        gg = torch.Generator().manual_seed(4000 + seed)
        m.train()
        for _ in range(STEPS):
            x, y = batch([3], 64, gg)
            loss = ce_loss(m(x), x, y)
            opt.zero_grad(); loss.backward(); opt.step()
        for k, p in m.named_parameters():
            if k not in keys and not torch.equal(p.detach(), orig[k]):
                die("frozen changed " + k)
        out["ladder"][name] = {"n_trainable": sum(p.numel() for p in tr), "rev_acc": acc_on(m, {3: ev[3]})[3]}
    for r in (32, 128, 512, 2048):
        torch.manual_seed(600 + seed)
        pk = Packet(r)
        gg = torch.Generator().manual_seed(4000 + seed)
        train(host, [3], STEPS, gg, packet=pk, lr=3e-3)
        out["ladder"][f"packet_r{r}"] = {"n_trainable": sum(p.numel() for p in pk.parameters()),
                                         "rev_acc": acc_on(host, {3: ev[3]}, packet=pk)[3]}
    # attention diagnostic
    x, _ = ev[3]
    mask = torch.full((L, L), float("-inf")).triu(1)
    diag = {}
    with torch.no_grad():
        h = host.emb(x) + host.pos(torch.arange(L))
        for bi, b in ((1, host.b1), (2, host.b2)):
            hh = b.ln1(h)
            W, Bi = b.attn.in_proj_weight, b.attn.in_proj_bias
            q = F.linear(hh, W[:D], Bi[:D]).view(-1, L, H, DH)
            k = F.linear(hh, W[D:2 * D], Bi[D:2 * D]).view(-1, L, H, DH)
            s = torch.einsum("blhd,bmhd->bhlm", q, k) / math.sqrt(DH) + mask
            p = torch.softmax(s, -1).mean(0)  # H, L, L
            for hd in range(H):
                mirror = sum(float(p[hd, 7 + i, 6 - i]) for i in range(6)) / 6
                copy_ = sum(float(p[hd, 7 + i, 1 + i]) for i in range(6)) / 6
                pos0 = sum(float(p[hd, 7 + i, 0]) for i in range(6)) / 6
                allx = sum(float(p[hd, 7 + i, 1:7].sum()) for i in range(6)) / 6
                diag[f"b{bi}h{hd}"] = {"mirror": round(mirror, 3), "copy_src": round(copy_, 3), "pos0": round(pos0, 3), "all_x": round(allx, 3)}
            a = mha_heads(b, hh, mask)
            h = h + a
            h = h + b.mlp(b.ln2(h))
    out["attn_diag"] = diag
    out["secs"] = round(time.time() - t0, 1)
    print(json.dumps(out), flush=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[3, 4, 5, 6])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = []
    for s in a.seeds:
        res.append(run(s))
        json.dump(res, open(a.out, "w"), indent=1)
