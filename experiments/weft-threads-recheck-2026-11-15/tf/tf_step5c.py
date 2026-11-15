"""tf_step5c.py : mechanism check for tf_step5b's finding that training only the block-1 MLP (attention frozen) learns REVERSE.
Hypothesis: the block-1 MLP rewrites position codes so that the FROZEN block-2 attention routes to the mirror position.
Test: after training mlp1 on REVERSE (2000 steps, lr 3e-3, CE true labels, everything else frozen), measure on REVERSE inputs
 (a) block-2 attention mass from query 7+i onto mirror source 6-i vs copy source 1+i, per head,
 (b) reverse accuracy with each block-2 head ablated (and all four),
 (c) same two measurements for the untouched host (should show copy_src high, mirror ~0).
Exits non-zero if a frozen parameter changed."""
import argparse, json
from tf_attn import *

def diag(model, x):
    mask = torch.full((L, L), float("-inf")).triu(1)
    out = {}
    with torch.no_grad():
        h = model.emb(x) + model.pos(torch.arange(L))
        for bi, b in ((1, model.b1), (2, model.b2)):
            hh = b.ln1(h)
            W, Bi = b.attn.in_proj_weight, b.attn.in_proj_bias
            q = F.linear(hh, W[:D], Bi[:D]).view(-1, L, H, DH)
            k = F.linear(hh, W[D:2 * D], Bi[D:2 * D]).view(-1, L, H, DH)
            s = torch.einsum("blhd,bmhd->bhlm", q, k) / math.sqrt(DH) + mask
            p = torch.softmax(s, -1).mean(0)
            for hd in range(H):
                out[f"b{bi}h{hd}"] = {"mirror": round(sum(float(p[hd, 7 + i, 6 - i]) for i in range(6)) / 6, 3),
                                      "copy_src": round(sum(float(p[hd, 7 + i, 1 + i]) for i in range(6)) / 6, 3)}
            h = h + mha_heads(b, hh, mask)
            h = h + b.mlp(b.ln2(h))
    return out

def run(seed):
    torch.manual_seed(100 + seed)
    g = torch.Generator().manual_seed(1000 + seed)
    host = train(TF(), [0, 1], 1200, g)
    for p in host.parameters(): p.requires_grad_(False)
    ge = torch.Generator().manual_seed(7000 + seed)
    ev = {3: batch([3], 512, ge)}
    m = copy.deepcopy(host)
    orig = {k: p.detach().clone() for k, p in host.named_parameters()}
    keys = [k for k, _ in m.named_parameters() if k.startswith("b1.up") or k.startswith("b1.down") or k.startswith("b1.ln2")]
    tr = []
    for k, p in m.named_parameters():
        p.requires_grad_(k in keys)
        if k in keys: tr.append(p)
    opt = torch.optim.AdamW(tr, lr=3e-3)
    gg = torch.Generator().manual_seed(4000 + seed)
    m.train()
    for _ in range(2000):
        x, y = batch([3], 64, gg)
        loss = ce_loss(m(x), x, y)
        opt.zero_grad(); loss.backward(); opt.step()
    for k, p in m.named_parameters():
        if k not in keys and not torch.equal(p.detach(), orig[k]): die("frozen changed " + k)
    m.eval()
    r = {"seed": seed, "rev_acc": acc_on(m, ev)[3],
         "attn_host": diag(host, ev[3][0]), "attn_tuned": diag(m, ev[3][0]), "ablate_rev_acc": {}}
    for ab in ([0], [1], [2], [3], [0, 1, 2, 3]):
        r["ablate_rev_acc"]["b2" + str(ab)] = acc_f(m, ev, ablate={2: ab})[3]
    for ab in ([0], [1], [2], [3], [0, 1, 2, 3]):
        r["ablate_rev_acc"]["b1" + str(ab)] = acc_f(m, ev, ablate={1: ab})[3]
    print(json.dumps(r), flush=True)
    return r

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, nargs="+", default=[3, 4, 5]); ap.add_argument("--out", required=True)
    a = ap.parse_args(); res = []
    for s in a.seeds:
        res.append(run(s)); json.dump(res, open(a.out, "w"), indent=1)
