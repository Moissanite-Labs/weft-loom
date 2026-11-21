"""Counts from a matched pair (second checker, numpy only). Reads out/pairs/<name>.npz, writes out/pairs/<name>.counts.json.

Per direction and tau in {0, 0.3, 0.5}: kept (|r| >= tau, r != 0), positive, negative, r == 0 dropped,
invariant statistic (mean |r| over kept), matched within the same layer, same-position count F, and the
inputs of the exact laws: per layer the multiset of n_j (same-layer cluster sizes) and the multiset of |s_j|
(signed cluster sums). Also mutual closest matches and pooled shares.
"""
import sys, os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAUS = [("0", 0.0), ("0.3", 0.3), ("0.5", 0.5)]


def layer_of(widths):
    off = np.concatenate([[0], np.cumsum(widths)])
    lay = np.concatenate([np.full(w, l) for l, w in enumerate(widths)])
    idx = np.arange(off[-1]) - off[lay]
    return lay, idx


def hist(values):
    u, c = np.unique(values, return_counts=True)
    return {str(int(a)): int(b) for a, b in zip(u, c)}


def direction(m, r, wsrc, wtgt):
    ls, isrc = layer_of(wsrc)
    lt, itgt = layer_of(wtgt)
    same_shape = len(wsrc) == len(wtgt) and all(a <= b for a, b in zip(wsrc, wtgt))
    out = {}
    for tname, tau in TAUS:
        nz = r != 0
        kept = nz & (np.abs(r) >= tau)
        pos = kept & (r > 0)
        d = {"kept": int(kept.sum()), "positive": int(pos.sum()), "negative": int((kept & (r < 0)).sum()),
             "r_exactly_zero": int((~nz).sum()),
             "invariant_mean_abs_r": float(np.abs(r[kept]).mean()) if kept.any() else None,
             "matched_same_layer": int((kept & (ls == lt[m])).sum())}
        # signed cluster sums over targets, for the cluster law (target side symmetric)
        c = np.where(r > 0, 1, -1)
        s = np.zeros(len(lt), dtype=np.int64)
        np.add.at(s, m[kept], c[kept])
        d["abs_s_hist"] = hist(np.abs(s[s != 0]))
        d["sum_s_sq"] = int(np.sum(s.astype(np.int64) ** 2))
        if same_shape:
            same = kept & (ls == lt[m]) & (isrc == itgt[m])
            d["same_position"] = int(same.sum())
            per = []
            for L in range(len(wsrc)):
                sel = kept & (ls == L) & (lt[m] == L)
                nj = np.bincount(m[sel], minlength=len(lt))
                nj = nj[nj > 0]
                per.append({"N": int(wtgt[L]), "n_hist": hist(nj)})
            d["same_position_layers"] = per
        out["tau_" + tname] = d
    return out


def main():
    name = sys.argv[1]
    z = np.load(os.path.join(ROOT, "out/pairs", name + ".npz"))
    wa = [int(x) for x in z["A_widths"]]; wb = [int(x) for x in z["B_widths"]]
    ab = direction(z["ab_m"], z["ab_r"], wa, wb)
    ba = direction(z["ba_m"], z["ba_r"], wb, wa)
    mutual = int((z["ba_m"][z["ab_m"]] == np.arange(len(z["ab_m"]))).sum())
    res = {"name": name, "nA": len(z["ab_m"]), "nB": len(z["ba_m"]), "ab": ab, "ba": ba,
           "mutual_closest": mutual}
    for tname, _ in TAUS:
        k = "tau_" + tname
        res["pooled_" + k] = [ab[k]["positive"] + ba[k]["positive"], ab[k]["kept"] + ba[k]["kept"]]
    with open(os.path.join(ROOT, "out/pairs", name + ".counts.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    for d, nm in ((ab, "ab"), (ba, "ba")):
        print(name, nm, " ".join("%s:%d/%d" % (k, d[k]["positive"], d[k]["kept"]) for k in d),
              "inv0 %.5f" % d["tau_0"]["invariant_mean_abs_r"], "F0", d["tau_0"].get("same_position"),
              "sameL0", d["tau_0"]["matched_same_layer"])
    print(name, "mutual", mutual, "/", len(z["ab_m"]))


if __name__ == "__main__":
    main()
