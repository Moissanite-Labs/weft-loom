"""Exploratory, post hoc (not in PLAN.txt): match each unit of A only within the same layer of B (float64, full
matrices), and report same position, share and the exact same-position null (per-layer relabelling).
Asked by the P4 miss: does matching over all layers lower the step-1000 same-position share?

Run: python -I within_layer.py <folder> <keyA> <keyB>
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exactlaw as X  # noqa: E402
from stats import flog10  # noqa: E402

ROOT, KA, KB = sys.argv[1], sys.argv[2], sys.argv[3]
RNG = np.random.Generator(np.random.PCG64(20261121))


def zl(key, L):
    a = np.load(os.path.join(ROOT, "traces", key, "L%02d.npy" % L)).astype(np.float64)
    a = a - a.mean(0)
    sd = np.sqrt((a ** 2).mean(0))
    live = sd > 0
    z = np.zeros_like(a)
    z[:, live] = a[:, live] / sd[live]
    return z, live


def main():
    files = sorted(f for f in os.listdir(os.path.join(ROOT, "traces", KA)) if f.startswith("L"))
    rows = []
    layers = []
    F = m = npos = 0
    for L in range(len(files)):
        za, la = zl(KA, L)
        zb, lb = zl(KB, L)
        R = za.T @ zb / za.shape[0]
        R[:, ~lb] = 0
        AR = np.abs(R)
        best = AR.max(1)
        tgt = np.empty(R.shape[0], dtype=np.int64)
        for i in range(R.shape[0]):
            tied = np.flatnonzero(AR[i] >= best[i] - 1e-12)
            tgt[i] = tied[0] if len(tied) == 1 else RNG.choice(tied)
        r = R[np.arange(R.shape[0]), tgt]
        keep = la & (r != 0)
        f = int((keep & (tgt == np.arange(R.shape[0]))).sum())
        js, cnt = np.unique(tgt[keep], return_counts=True)
        layers.append((zb.shape[1], [int(c) for c in cnt]))
        rows.append({"layer": L, "kept": int(keep.sum()), "same_position": f, "positive": int((r[keep] > 0).sum())})
        F += f; m += int(keep.sum()); npos += int((r[keep] > 0).sum())
    t = X.same_position_test(layers, F)
    out = {"A": KA, "B": KB, "note": "post hoc, within-layer matching, tau 0", "same_position": {"num": F, "den": m},
           "share": {"num": npos, "den": m}, "null_mean": "%d/%d" % (t["mean"].numerator, t["mean"].denominator),
           "per_layer": rows}
    if "p_upper" in t:
        out["p_upper"] = flog10(t["p_upper"])
    elif "bracket" in t:
        out["p_upper_bracket"] = [flog10(t["bracket"][0]), flog10(t["bracket"][1])]
    else:
        out["p_upper_bound"] = flog10(t["bound_upper"])
    os.makedirs(os.path.join(ROOT, "out", "within_layer"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "out", "within_layer", KA + "__" + KB + ".json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "per_layer"}))


if __name__ == "__main__":
    main()
