"""Analysis for Statement S5 (sampled evidence). Exact p-values per pair via exact_null.

Usage (venv):  python -I analyze.py
Reads ../runs/*.npz, writes ../out/analysis.json and ../out/pairs.jsonl.
"""
import json
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import torch  # noqa: E402
import nets  # noqa: E402
import exact_null as ex  # noqa: E402


def _opt(name, default):
    """Folder option from the command line (for example --out DIR), with the record's layout as default."""
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument(name, default=default)
    known, rest = ap.parse_known_args()
    sys.argv[1:] = rest
    return getattr(known, name.lstrip("-").replace("-", "_"))


RUNS = _opt("--runs", os.path.join(HERE, "..", "runs"))
OUT = _opt("--out", os.path.join(HERE, "..", "out"))
TAUS = (0.0, 0.3, 0.5)
PROBE = nets.probe_set()
torch.set_num_threads(8)

_params = {}
_traces = {}


def kind_of(fname):
    if fname.startswith("plain_relu"):
        return "plain", "relu"
    if fname.startswith("plain_gelu"):
        return "plain", "gelu"
    if fname.startswith("plain_tanh"):
        return "plain", "tanh"
    return "gated", "silu"


def traces(fname, idx):
    key = (fname, idx)
    if key in _traces:
        return _traces[key]
    if fname not in _params:
        _params[fname] = nets.load(os.path.join(RUNS, fname + ".npz"))[0]
    P = {k: v[idx:idx + 1] for k, v in _params[fname].items()}
    block, act = kind_of(fname)
    hid, res = nets.traces_of(P, block, act, PROBE)
    val = ([x[0] for x in hid], [x[0] for x in res])
    if len(_traces) > 64:
        _traces.clear()
    _traces[key] = val
    return val


def zscore(X):
    """Columns standardised; columns with (near) zero variance are dropped (an
    invariant criterion: it does not depend on any unit's sign or position)."""
    mu = X.mean(0)
    sd = X.std(0)
    keep = sd > 1e-8 * max(1.0, float(sd.max()))
    Z = (X[:, keep] - mu[keep]) / sd[keep]
    return Z, np.nonzero(keep)[0]


def match_layer(XA, XB):
    ZA, ia = zscore(XA)
    ZB, ib = zscore(XB)
    C = ZA.T @ ZB / ZA.shape[0]
    j = np.abs(C).argmax(1)
    c = C[np.arange(C.shape[0]), j]
    return ia, ib[j], c, np.abs(C).max(1)


def pair_stats(fa, ia, fb, ib):
    hA, rA = traces(fa, ia)
    hB, rB = traces(fb, ib)
    rec = {"A": [fa, int(ia)], "B": [fb, int(ib)]}
    # hidden-unit sign test, pooled over layers; B unit identity = (layer, j)
    units = []  # (layer, a_index, b_index, corr)
    for l in range(len(hA)):
        a_idx, b_idx, c, _ = match_layer(hA[l], hB[l])
        for a, b, cc in zip(a_idx, b_idx, c):
            units.append((l, int(a), int(b), float(cc)))
    for tau in TAUS:
        kept = [u for u in units if abs(u[3]) >= tau]
        if not kept:
            rec["tau%.1f" % tau] = None
            continue
        matches = [(u[0], u[2]) for u in kept]
        signs = [1 if u[3] > 0 else -1 for u in kept]
        cp = ex.cluster_pvalues(matches, signs)
        m, npos = cp["m"], cp["npos"]
        rec["tau%.1f" % tau] = {
            "m": m, "npos": npos, "share": npos / m, "J": cp["J"], "sum_s2": cp["sum_s2"],
            "p_bin_up": float(ex.binom_upper(m, npos)), "p_bin_two": float(ex.binom_two_sided(m, npos)),
            "p_clu_up": float(cp["p_upper"]), "p_clu_two": float(cp["p_two"]),
        }
    # same-position count with exact rook law, per layer then convolved (layers' permutations independent)
    law_tot = [Fraction(1)]
    F_tot = 0
    for l in range(len(hA)):
        h = hB[l].shape[1]
        layer_units = [u for u in units if u[0] == l]
        F_tot += sum(1 for u in layer_units if u[1] == u[2])
        sizes = {}
        for u in layer_units:
            sizes[u[2]] = sizes.get(u[2], 0) + 1
        law = ex.same_position_law(list(sizes.values()), h)
        new = [Fraction(0)] * (len(law_tot) + len(law) - 1)
        for x, p in enumerate(law_tot):
            for y, q in enumerate(law):
                new[x + y] += p * q
        law_tot = new
    rec["same_pos"] = {"F": F_tot, "p_up": float(ex.tail_upper(law_tot, F_tot))}
    # residual-coordinate sign test: one residual group for all layers -> key = coordinate k
    rmatch, rsign = [], []
    for l in range(len(rA)):
        a_idx, b_idx, c, _ = match_layer(rA[l], rB[l])
        for b, cc in zip(b_idx, c):
            rmatch.append(int(b))
            rsign.append(1 if cc > 0 else -1)
    cp = ex.cluster_pvalues(rmatch, rsign)
    rec["resid"] = {"m": cp["m"], "npos": cp["npos"], "share": cp["npos"] / cp["m"],
                    "p_clu_up": float(cp["p_upper"]), "p_bin_up": float(ex.binom_upper(cp["m"], cp["npos"]))}
    # group-invariant statistic: mean over A units of max_j |corr|
    rec["inv_mean_maxabs"] = float(np.mean([abs(u[3]) for u in units]))
    rec["inv_share_gt_0.9"] = float(np.mean([abs(u[3]) > 0.9 for u in units]))
    return rec


def diagnostics(fname, idx):
    hA, _ = traces(fname, idx)
    out = []
    for X in hA:
        pos = np.clip(X, 0, None).mean(0)
        neg = np.clip(-X, 0, None).mean(0)
        tot = pos + neg
        live = tot > 1e-12
        rho = np.minimum(pos, neg)[live] / tot[live]
        mean = X.mean(0)[live]
        h_eff = int(live.sum())
        npos_mean = int((mean > 0).sum())
        out.append({"h_live": h_eff, "two_sided_share_rho_ge_0.1": float((rho >= 0.1).mean()),
                    "rho_median": float(np.median(rho)), "n_positive_mean": npos_mean,
                    "lean_p_two": float(ex.binom_two_sided(h_eff, npos_mean))})
    return out


def summarise(recs, tau_keys=("tau0.0", "tau0.3", "tau0.5")):
    S = {"n_pairs": len(recs)}
    for tk in tau_keys:
        rows = [r[tk] for r in recs if r.get(tk)]
        if not rows:
            continue
        sh = np.array([x["share"] for x in rows])
        m = np.array([x["m"] for x in rows])
        S[tk] = {
            "m_median": float(np.median(m)), "m_min": int(m.min()),
            "share_mean": float(sh.mean()), "share_sd": float(sh.std(ddof=1)) if len(sh) > 1 else 0.0,
            "share_min": float(sh.min()), "share_max": float(sh.max()),
            "binomial_sd_pred_median": float(np.median(0.5 / np.sqrt(m))),
            "cluster_sd_pred_median": float(np.median([np.sqrt(x["sum_s2"]) / (2 * x["m"]) for x in rows])),
            "kappa_median": float(np.median([x["sum_s2"] / x["m"] for x in rows])),
        }
        for pk in ("p_bin_up", "p_clu_up", "p_bin_two", "p_clu_two"):
            p = np.array([x[pk] for x in rows])
            S[tk][pk] = {"lt_0.05": float((p < 0.05).mean()), "lt_0.01": float((p < 0.01).mean()),
                         "n_lt_0.05": int((p < 0.05).sum()), "n_lt_0.01": int((p < 0.01).sum())}
    sp = np.array([r["same_pos"]["p_up"] for r in recs])
    S["same_pos"] = {"F_mean": float(np.mean([r["same_pos"]["F"] for r in recs])),
                     "F_max": int(max(r["same_pos"]["F"] for r in recs)),
                     "p_lt_0.05": float((sp < 0.05).mean()), "p_lt_0.01": float((sp < 0.01).mean())}
    rp = np.array([r["resid"]["p_clu_up"] for r in recs])
    S["resid"] = {"share_mean": float(np.mean([r["resid"]["share"] for r in recs])),
                  "p_clu_lt_0.05": float((rp < 0.05).mean()), "p_clu_lt_0.01": float((rp < 0.01).mean())}
    inv = np.array([r["inv_mean_maxabs"] for r in recs])
    S["inv_mean_maxabs"] = {"mean": float(inv.mean()), "min": float(inv.min()), "max": float(inv.max())}
    return S


def main():
    plan = {}
    plan["null_h128_disjoint"] = [("null_h128", 2 * k, "null_h128", 2 * k + 1) for k in range(200)]
    plan["null_h64_disjoint"] = [("null_h64", 2 * k, "null_h64", 2 * k + 1) for k in range(50)]
    plan["null_h256_disjoint"] = [("null_h256", 2 * k, "null_h256", 2 * k + 1) for k in range(50)]
    plan["null_other_data_order"] = [("null_h128", k, "null_otherorder", k) for k in range(100)]
    plan["null_fixedA_gated"] = [("null_h128", 0, "null_h128", 200 + k) for k in range(200)]
    # replications added after the first fixed-A run showed 8/200 cluster p < 0.01 at tau 0.3
    for a in (2, 4, 6, 8):
        plan["null_fixedA_gated_rep%d" % a] = [("null_h128", a, "null_h128", 200 + k) for k in range(200)]
    plan["plain_relu_disjoint"] = [("plain_relu", 2 * k, "plain_relu", 2 * k + 1) for k in range(100)]
    plan["plain_gelu_disjoint"] = [("plain_gelu", 2 * k, "plain_gelu", 2 * k + 1) for k in range(100)]
    plan["plain_tanh_disjoint"] = [("plain_tanh", 2 * k, "plain_tanh", 2 * k + 1) for k in range(50)]
    plan["mixed_A_gelu_B_gated"] = [("plain_gelu", k, "null_h128", 200 + k) for k in range(100)]
    plan["mixed_fixedA_gelu_B_gated"] = [("plain_gelu", 0, "null_h128", 200 + k) for k in range(200)]
    plan["mixed_A_gated_B_gelu"] = [("null_h128", 200 + k, "plain_gelu", 100 + k) for k in range(100)]
    plan["siblings_same_init_other_order"] = [("null_h128", k, "siblings", k) for k in range(40)]
    for task in ("same", "diff"):
        for K in (30, 300, 3000):
            plan["descend_%s_%d" % (task, K)] = [("null_h128", k, "descend_%s_%d" % (task, K), k) for k in range(40)]
    for variant in ("hidden", "full"):
        for stage in ("0", "same300", "diff3000"):
            plan["planted_%s_%s" % (variant, stage)] = [("null_h128", 40 + k, "planted_%s_%s" % (variant, stage), k)
                                                       for k in range(40)]
    only = sys.argv[1:]
    tag = "_".join(only) if only else "all"
    results = {}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "pairs_%s.jsonl" % tag), "w") as fp:
        for name, pairs in plan.items():
            if only and name not in only:
                continue
            if not all(os.path.exists(os.path.join(RUNS, f + ".npz")) for f in {p[0] for p in pairs} | {p[2] for p in pairs}):
                results[name] = "missing runs"
                continue
            recs = [pair_stats(*p) for p in pairs]
            for r in recs:
                fp.write(json.dumps({"exp": name, **r}, sort_keys=True) + "\n")
            results[name] = summarise(recs)
            print(name, json.dumps(results[name].get("tau0.0", {}))[:400], flush=True)
    # per-model diagnostics
    diag = {}
    for fname, n in (("null_h128", 100), ("plain_relu", 100), ("plain_gelu", 100), ("plain_tanh", 100),
                     ("null_h64", 50), ("null_h256", 50)):
        if not os.path.exists(os.path.join(RUNS, fname + ".npz")):
            continue
        ds = [diagnostics(fname, k) for k in range(n)]
        flat = [x for d in ds for x in d]
        lp = np.array([x["lean_p_two"] for x in flat])
        diag[fname] = {
            "n_model_layers": len(flat),
            "two_sided_share_mean": float(np.mean([x["two_sided_share_rho_ge_0.1"] for x in flat])),
            "two_sided_share_min": float(np.min([x["two_sided_share_rho_ge_0.1"] for x in flat])),
            "two_sided_share_max": float(np.max([x["two_sided_share_rho_ge_0.1"] for x in flat])),
            "rho_median_mean": float(np.mean([x["rho_median"] for x in flat])),
            "positive_mean_share_mean": float(np.mean([x["n_positive_mean"] / x["h_live"] for x in flat])),
            "lean_p_lt_0.05": float((lp < 0.05).mean()), "lean_p_lt_0.01": float((lp < 0.01).mean()),
        }
    results["diagnostics_per_model_layer"] = diag
    with open(os.path.join(OUT, "analysis_%s.json" % tag), "w") as f:
        json.dump(results, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
