"""tf_step5.py : test the stated explanation for REVERSE directly.
Claim under test: "a position-wise packet cannot move data across positions; REVERSE lives in attention".
Test: host (COPY+ADD3, trained as in tf_seeds.py for the same seed) gets its attention (in_proj, out_proj, ln1) frozen
and the listed parameter groups trained with CE on the task for STEPS steps (lr 2e-3, batch 64, AdamW).
 mlp      : both MLPs (up, down), ln2 x2, final LN, readout head. Embeddings and position embeddings frozen.
 mlp_emb  : mlp + token and position embeddings (position embeddings can re-route attention, so this is looser)
 full     : everything trainable, reverse (control that REVERSE is learnable from the host init in this budget)
 mlp@mul5 : mlp group on MUL5 (positive control that the setup can learn a position-wise skill)
Explanation stands for 'mlp' if final REVERSE acc stays far below 1.0 while the controls succeed.
The script exits non-zero if a frozen parameter changed or the functional forward disagrees with the model.
"""
import argparse
import json
import time

from tf_attn import *  # noqa

STEPS = 3000


def groups(model, name):
    ps = {k: p for k, p in model.named_parameters()}
    def sel(f):
        return [p for k, p in ps.items() if f(k)]
    if name == "full":
        return list(ps.values())
    mlp = lambda k: (".up." in k or ".down." in k or ".ln2." in k or k.startswith("lnf") or k.startswith("head"))
    if name == "mlp":
        return sel(mlp)
    if name == "mlp_emb":
        return sel(lambda k: mlp(k) or k.startswith("emb") or k.startswith("pos"))
    die("group")


def run(seed):
    t0 = time.time()
    torch.manual_seed(100 + seed)
    g = torch.Generator().manual_seed(1000 + seed)
    host = train(TF(), [0, 1], 1200, g)
    ge = torch.Generator().manual_seed(7000 + seed)
    ev = {t: batch([t], 512, ge) for t in (0, 1, 2, 3)}
    parity_check(host, ev[3][0])
    host_acc = acc_on(host, ev)
    out = {"seed": seed, "host_acc": host_acc, "variants": {}}
    for name, task in (("mlp", 3), ("mlp_emb", 3), ("full", 3), ("mlp", 2)):
        m = copy.deepcopy(host)
        orig = {k: p.detach().clone() for k, p in host.named_parameters()}
        tr = groups(m, name)
        trset = {id(p) for p in tr}
        opt = torch.optim.AdamW(tr, lr=2e-3)
        gg = torch.Generator().manual_seed(4000 + seed)
        curve = []
        m.train()
        for step in range(STEPS + 1):
            if step % 250 == 0:
                curve.append((step, acc_on(m, {task: ev[task]})[task]))
                m.train()
            if step == STEPS:
                break
            x, y = batch([task], 64, gg)
            loss = ce_loss(m(x), x, y)
            opt.zero_grad(); loss.backward(); opt.step()
        for k, p in m.named_parameters():
            if id(p) not in trset and not torch.equal(p.detach(), orig[k]):
                die("frozen parameter changed: " + k)
        final = acc_on(m, ev)
        out["variants"][f"{name}@{'rev' if task == 3 else 'mul5'}"] = {
            "n_trainable": sum(p.numel() for p in tr), "final": final, "curve": curve}
    out["secs"] = round(time.time() - t0, 1)
    print(json.dumps(out), flush=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=list(range(3, 11)))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = []
    for s in a.seeds:
        res.append(run(s))
        json.dump(res, open(a.out, "w"), indent=1)
