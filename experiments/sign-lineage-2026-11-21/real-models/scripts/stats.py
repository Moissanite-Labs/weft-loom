"""Statistics of PLAN.txt section (d) from traces (per model) and from the match files (per pair).

Run: python -I stats.py <folder> models <key>...      -> out/models/<key>.json
     python -I stats.py <folder> pair <name>           -> out/stats/<name>.json
"""
import json
import math
import os
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exactlaw as X  # noqa: E402

ROOT = sys.argv[1]
GATED = {"s135", "s135i", "s360", "s135L", "falcon", "q08", "q2"}
TAUS = [("0", 0.0), ("0.3", 0.3), ("0.5", 0.5)]


def flog10(p):
    """Decimal string of a nonnegative Fraction, exact to the digits shown (via integer arithmetic)."""
    p = Fraction(p)
    if p == 0:
        return "0"
    if p >= Fraction(1, 10 ** 300):
        return "%.6e" % float(p)
    n, d = p.numerator, p.denominator
    en = max(0, n.bit_length() - 60); ed = max(0, d.bit_length() - 60)
    lg = math.log10(n >> en) - math.log10(d >> ed) + (en - ed) * math.log10(2)
    e = math.floor(lg)
    return "%.4fe%d (display rounded)" % (10 ** (lg - e), e)


def rate(a, b):
    return {"num": int(a), "den": int(b)}


def model_stats(key):
    d = os.path.join(ROOT, "traces", key)
    files = sorted(f for f in os.listdir(d) if f.startswith("L") and f.endswith(".npy"))
    per_layer = []
    tot_pos = tot_live = tot_mpos = tot_lean90 = tot_units = tot_zero = 0
    for f in files:
        a = np.load(os.path.join(d, f)).astype(np.float64)
        mu = a.mean(0)
        c = a - mu
        var = (c ** 2).mean(0)
        m3 = (c ** 3).mean(0)
        live = (var > 0) & (m3 != 0)
        pos = int(((m3 > 0) & live).sum())
        nlive = int(live.sum())
        mpos = int(((mu > 0) & (var > 0)).sum())
        lean90 = int((((a > 0).mean(0) > 0.9) & (var > 0)).sum())
        per_layer.append({"layer": f[1:3], "h": a.shape[1], "skew_pos": pos, "live": nlive,
                          "mean_pos": mpos, "pos_on_gt90pct_words": lean90, "zero_var": int((var == 0).sum())})
        tot_pos += pos; tot_live += nlive; tot_mpos += mpos; tot_lean90 += lean90; tot_units += a.shape[1]
        tot_zero += int((var == 0).sum())
    bt = X.binom_test(tot_live, tot_pos)
    out = {"key": key, "units": tot_units, "zero_var": tot_zero,
           "skew_positive": rate(tot_pos, tot_live),
           "skew_p_two": flog10(bt["p_two"]), "skew_p_two_ge_0.001": bool(bt["p_two"] >= Fraction(1, 1000)),
           "skew_test": "pass" if bt["p_two"] >= Fraction(1, 1000) else "fail",
           "mean_positive": rate(tot_mpos, tot_units - tot_zero),
           "pos_on_gt90pct_words": rate(tot_lean90, tot_units - tot_zero),
           "per_layer": per_layer}
    # per-layer skew p (two-sided), for the record
    for pl in out["per_layer"]:
        b = X.binom_test(pl["live"], pl["skew_pos"])
        pl["skew_p_two"] = flog10(b["p_two"])
    os.makedirs(os.path.join(ROOT, "out", "models"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "out", "models", key + ".json"), "w"), indent=1)
    print(key, out["skew_positive"], out["skew_test"], out["skew_p_two"], "lean90", out["pos_on_gt90pct_words"])


def model_info(key):
    p = os.path.join(ROOT, "out", "models", key + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def direction(src_key, tgt_key, src, tgt, r, Al, Ai, Bl, Bi, Bwidths, same_shape):
    res = {"source": src_key, "target": tgt_key}
    si = model_info(src_key); ti = model_info(tgt_key)
    src_sym = src_key in GATED and si is not None and si["skew_test"] == "pass"
    tgt_sym = tgt_key in GATED and ti is not None and ti["skew_test"] == "pass"
    res["law"] = "binomial (source gated, passes skew)" if src_sym else (
        "cluster (target gated, passes skew)" if tgt_sym else "none")
    nz = r != 0
    res["dropped_r_exactly_zero"] = int((~nz).sum())
    for name, tau in TAUS:
        keep = nz & (np.abs(r) >= tau)
        m = int(keep.sum()); npos = int((r[keep] > 0).sum())
        e = {"share": rate(npos, m), "invariant_mean_max_abs_r": float(np.abs(r[keep]).mean()) if m else None}
        same_layer = int((Al[src[keep]] == Bl[tgt[keep]]).sum())
        e["matched_same_layer"] = rate(same_layer, m)
        if m and res["law"].startswith("binomial"):
            b = X.binom_test(m, npos)
            e["p_upper"] = flog10(b["p_upper"]); e["p_two"] = flog10(b["p_two"])
            e["inside_999_band"] = bool(b["p_two"] >= Fraction(1, 1000))
        elif m and res["law"].startswith("cluster"):
            s = {}
            for j, sg in zip(tgt[keep], np.sign(r[keep]).astype(int)):
                s[int(j)] = s.get(int(j), 0) + int(sg)
            sv = list(s.values())
            c = X.cluster_test(sv, m, npos)
            e["clusters"] = len(sv)
            e["kappa_num_den"] = rate(sum(v * v for v in sv), m)
            if c["exact"]:
                e["p_upper"] = flog10(c["p_upper"]); e["p_two"] = flog10(c["p_two"])
                e["inside_999_band"] = bool(c["p_two"] >= Fraction(1, 1000))
                e["p_exact"] = True
            else:
                e["p_exact"] = False
                e["hoeffding_upper"] = c["hoeffding_upper"]; e["hoeffding_two"] = c["hoeffding_two"]
                e["inside_999_band"] = None if c["hoeffding_two"] >= 0.001 else False
                e["cluster_cost"] = c["cost"]
        if same_shape:
            same = keep & (Al[src] == Bl[tgt]) & (Ai[src] == Bi[tgt])
            F = int(same.sum())
            e["same_position"] = rate(F, m)
            if name in ("0", "0.3"):
                layers = []
                for L in range(len(Bwidths)):
                    sel = keep & (Al[src] == L) & (Bl[tgt] == L)
                    js, cnt = np.unique(tgt[sel], return_counts=True)
                    layers.append((Bwidths[L], [int(x) for x in cnt]))
                t = X.same_position_test(layers, F)
                e["same_position_null_mean"] = "%.4f" % float(t["mean"])
                e["same_position_null_mean_exact"] = "%d/%d" % (t["mean"].numerator, t["mean"].denominator)
                if "p_upper" in t:
                    e["same_position_p_upper"] = flog10(t["p_upper"]); pu = t["p_upper"]
                elif "bracket" in t:
                    e["same_position_p_upper_bracket"] = [flog10(t["bracket"][0]), flog10(t["bracket"][1])]
                    pu = t["bracket"][1]
                else:
                    e["same_position_p_upper_bound"] = flog10(t["bound_upper"]) + " (" + t["bound_kind"] + ")"
                    pu = t["bound_upper"]
                e["same_position_inside_null"] = bool(pu >= Fraction(1, 1000)) if "bracket" not in t else (
                    True if t["bracket"][0] >= Fraction(1, 1000) else (False if pu < Fraction(1, 1000) else None))
        res["tau_" + name] = e
    return res


def pair_stats(name):
    meta = json.load(open(os.path.join(ROOT, "out", "pairs", name + ".json")))
    z = np.load(os.path.join(ROOT, "out", "pairs", name + ".npz"))
    KA, KB = meta["A"], meta["B"]
    if meta.get("shuffle") is not None:
        KBs = KB  # same model, words permuted
    else:
        KBs = KB
    Al, Ai, Bl, Bi = z["A_layer"], z["A_index"], z["B_layer"], z["B_index"]
    same_shape_ab = meta["A_layers"] == meta["B_layers"] and all(
        a <= b for a, b in zip(meta["A_widths"], meta["B_widths"]))
    same_shape_ba = meta["A_layers"] == meta["B_layers"] and all(
        b <= a for a, b in zip(meta["A_widths"], meta["B_widths"]))
    out = {"name": name, "pair_meta": meta}
    out["ab"] = direction(KA, KBs, z["ab_src"], z["ab_tgt"], z["ab_r"], Al, Ai, Bl, Bi, meta["B_widths"], same_shape_ab)
    out["ba"] = direction(KBs, KA, z["ba_src"], z["ba_tgt"], z["ba_r"], Bl, Bi, Al, Ai, meta["A_widths"], same_shape_ba)
    # mutual closest matches (tau 0)
    back = dict(zip(z["ba_src"].tolist(), z["ba_tgt"].tolist()))
    mut = sum(1 for s, t in zip(z["ab_src"].tolist(), z["ab_tgt"].tolist()) if back.get(t) == s)
    out["mutual_closest"] = rate(mut, len(z["ab_src"]))
    # pooled over both directions (refuter alternative e)
    for name_t, tau in TAUS:
        k1 = (z["ab_r"] != 0) & (np.abs(z["ab_r"]) >= tau); k2 = (z["ba_r"] != 0) & (np.abs(z["ba_r"]) >= tau)
        out["pooled_share_tau_" + name_t] = rate(int((z["ab_r"][k1] > 0).sum() + (z["ba_r"][k2] > 0).sum()),
                                                 int(k1.sum() + k2.sum()))
    os.makedirs(os.path.join(ROOT, "out", "stats"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "out", "stats", name + ".json"), "w"), indent=1)
    for dname in ("ab", "ba"):
        dd = out[dname]
        print(name, dname, dd["law"], {k: (v["share"], v.get("p_two"), v.get("same_position"),
                                           v.get("invariant_mean_max_abs_r"))
                                       for k, v in dd.items() if k.startswith("tau_")})
    print(name, "mutual", out["mutual_closest"])


if __name__ == "__main__":
    if sys.argv[2] == "models":
        for k in sys.argv[3:]:
            model_stats(k)
    else:
        for n in sys.argv[3:]:
            pair_stats(n)
