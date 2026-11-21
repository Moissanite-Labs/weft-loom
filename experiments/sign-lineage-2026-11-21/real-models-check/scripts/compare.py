"""Exact p-values for my counts, number-by-number comparison with the first agent's outputs, and re-scoring of
every prediction by PLAN.txt's written rules. Pure Python (exact.py) plus json; no numpy needed.

Reads: out/models/*.json, out/pairs/*.counts.json, out/within_*.json, out/hook/*.json (mine);
       real-models/out/stats/*.json, real-models/RESULTS.json, real-models/out/within_layer/*.json (theirs).
Writes: out/compare.json and prints a table.
"""
import sys, os, json
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exact  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# --real-models DIR: the first run's folder (traces/, hf/, data/, out/). Default: ../../real-models next to this
# folder in the published record. The option is removed from sys.argv before the positional arguments are read.
import argparse as _argparse
_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--real-models", default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "real-models"))
_known, _rest = _ap.parse_known_args()
sys.argv = sys.argv[:1] + _rest
RM = _known.real_models
GATED = {"s135", "s135i", "s135L", "s360", "falcon", "q08", "q2"}  # product traces of gated blocks
TAUS = ["tau_0", "tau_0.3", "tau_0.5"]
PAIRS = ["s135__s135i", "s135__s360", "s135__s135L", "py__py_s1", "py__py_s2", "py_s1__py_s2", "py_1k__py",
         "py_8k__py", "py_32k__py", "py__falcon", "py__falcon_gate", "s135__s135", "s135__s135i_shuf", "q08__q2",
         "py__s135", "falcon__s135", "s135__mylaund5150"]
THEIRS_POSTHOC = {"py__s135", "falcon__s135"}
mism = []
rows = []


def J(p):
    with open(p) as fh:
        return json.load(fh)


def cmp(what, mine, theirs, tol=None):
    if theirs is None:
        rows.append((what, mine, "-", "n/a"))
        return
    if tol is None:
        ok = mine == theirs
    else:
        ok = abs(float(mine) - float(theirs)) <= tol
    rows.append((what, mine, theirs, "ok" if ok else "DIFF"))
    if not ok:
        mism.append((what, mine, theirs))


def pval_str_close(mine_frac, theirs_str):
    """Their p strings: '%.6e' or 'x.xxxxe-NNNN (display rounded)'. Compare to 4 significant digits in log."""
    if theirs_str is None:
        return None
    s = str(theirs_str).split(" ")[0]
    mant, _, ex = s.partition("e")
    from math import log10
    lt = log10(float(mant)) + int(ex)
    lm = exact.log10_fraction(mine_frac)
    return abs(lt - lm) < 2e-4 * max(1.0, abs(lt))


model_stats = {}
for f in sorted(os.listdir(os.path.join(ROOT, "out/models"))):
    if f.endswith(".json"):
        d = J(os.path.join(ROOT, "out/models", f))
        nz = d["skew_pos"] + d["skew_neg"]
        p = exact.binom_two_sided(nz, d["skew_pos"])
        d["skew_p_two"] = p
        d["skew_pass"] = p >= Fraction(1, 1000)
        model_stats[d["key"]] = d
theirs_res = J(os.path.join(RM, "RESULTS.json"))
for k, d in model_stats.items():
    t = theirs_res["models"].get(k)
    if t is None:
        continue
    cmp("model %s skew+" % k, [d["skew_pos"], d["skew_pos"] + d["skew_neg"]], [t["skew_positive"]["num"], t["skew_positive"]["den"]])
    okp = pval_str_close(d["skew_p_two"], t["skew_p_two"])
    rows.append(("model %s skew p two" % k, exact.fmt(d["skew_p_two"]), t["skew_p_two"], "ok" if okp else "DIFF"))
    if not okp:
        mism.append(("model %s skew p two" % k, exact.fmt(d["skew_p_two"]), t["skew_p_two"]))
    cmp("model %s skew verdict" % k, "pass" if d["skew_pass"] else "fail", t["skew_test"])
    cmp("model %s mean+" % k, d["mean_pos"], t["mean_positive"]["num"])
    cmp("model %s >90%% positive" % k, d["pos_on_gt90pct_words"], t["pos_on_gt90pct_words"]["num"])


def law_for(src, tgt):
    s0 = src.split("_shuf")[0]
    t0 = tgt.split("_shuf")[0]
    if s0 in GATED and model_stats[s0]["skew_pass"]:
        return "binomial"
    if t0 in GATED and model_stats[t0]["skew_pass"]:
        return "cluster"
    return "none"


mine_pairs = {}
for name in PAIRS:
    pth = os.path.join(ROOT, "out/pairs", name + ".counts.json")
    if not os.path.exists(pth):
        print("missing", name)
        continue
    c = J(pth)
    a_key, b_key = name.split("__")
    if b_key == "mylaund5150":
        b_key = "s135i"
    if b_key == "s135i_shuf":
        b_key = "s135i"
    res = {"name": name}
    for dname, src, tgt in (("ab", a_key, b_key), ("ba", b_key, a_key)):
        law = law_for(src, tgt)
        dd = {"law": law}
        for t in TAUS:
            x = c[dname][t]
            m, pos = x["kept"], x["positive"]
            e = {"kept": m, "positive": pos, "invariant": x["invariant_mean_abs_r"],
                 "matched_same_layer": x["matched_same_layer"], "r_zero": x["r_exactly_zero"]}
            if m > 0 and law == "binomial":
                lo, up = exact.binom_tails(m, pos)
                e["p_upper"] = up; e["p_two"] = min(Fraction(1), 2 * min(lo, up))
            elif m > 0 and law == "cluster":
                s_obs = 2 * pos - m
                lo, up = exact.cluster_tails(x["abs_s_hist"], s_obs)
                e["p_upper"] = up; e["p_two"] = min(Fraction(1), 2 * min(lo, up))
                e["kappa"] = Fraction(x["sum_s_sq"], m)
            if "same_position" in x and t in ("tau_0", "tau_0.3"):
                F = x["same_position"]
                layers = [(l["N"], l["n_hist"]) for l in x["same_position_layers"]]
                e["F"] = F
                e["null_mean"] = exact.same_pos_mean(layers)
                if F <= 300:
                    e["F_p_upper"] = exact.same_pos_upper(layers, F)
                    e["F_p_kind"] = "bracket"
                else:
                    ok, l10 = exact.factorial_bound_small(len(layers), F)
                    e["F_bound_below_0.001"] = ok
                    e["F_bound_log10"] = l10
                    e["F_p_kind"] = "bound L^k/k!"
            elif "same_position" in x:
                e["F"] = x["same_position"]
            dd[t] = e
        res[dname] = dd
    res["mutual"] = c["mutual_closest"]
    res["nA"] = c["nA"]
    res["pooled"] = {t: c["pooled_" + t] for t in TAUS}
    mine_pairs[name] = res
    # compare with theirs
    tp = os.path.join(RM, "out/stats", name + ".json")
    th = J(tp) if os.path.exists(tp) else None
    if th is None:
        continue
    for dname in ("ab", "ba"):
        for t in TAUS:
            me = res[dname][t]; tt = th[dname].get(t, {})
            sh = tt.get("share")
            cmp("%s %s %s share" % (name, dname, t), [me["positive"], me["kept"]], [sh["num"], sh["den"]] if sh else None)
            inv = tt.get("invariant_mean_max_abs_r")
            if inv is not None:
                cmp("%s %s %s invariant" % (name, dname, t), round(me["invariant"], 6), round(float(inv), 6), tol=2e-6)
            ms = tt.get("matched_same_layer")
            if ms:
                cmp("%s %s %s same-layer" % (name, dname, t), me["matched_same_layer"], ms["num"])
            sp = tt.get("same_position")
            if sp and "F" in me:
                cmp("%s %s %s same position" % (name, dname, t), me["F"], sp["num"])
            if "null_mean" in me and tt.get("same_position_null_mean_exact"):
                cmp("%s %s %s null mean" % (name, dname, t), me["null_mean"], Fraction(tt["same_position_null_mean_exact"]))
            if "F_p_upper" in me and tt.get("same_position_p_upper_bracket"):
                lo, hi = me["F_p_upper"]
                tlo, thi = [float(v.split(" ")[0]) for v in tt["same_position_p_upper_bracket"]]
                inside = (tlo * (1 - 1e-6) <= float(lo)) and (float(hi) <= thi * (1 + 1e-6))
                rows.append(("%s %s %s F p bracket (mine inside theirs)" % (name, dname, t),
                             [exact.fmt(lo), exact.fmt(hi)], tt["same_position_p_upper_bracket"], "ok" if inside else "DIFF"))
                if not inside:
                    mism.append(("%s %s %s F p bracket" % (name, dname, t), [exact.fmt(lo), exact.fmt(hi)], tt["same_position_p_upper_bracket"]))
            if "p_two" in me and tt.get("p_two") is not None:
                ok = pval_str_close(me["p_two"], tt["p_two"])
                rows.append(("%s %s %s p_two" % (name, dname, t), exact.fmt(me["p_two"]), tt["p_two"], "ok" if ok else "DIFF"))
                if not ok:
                    mism.append(("%s %s %s p_two" % (name, dname, t), exact.fmt(me["p_two"]), tt["p_two"]))
            if "p_upper" in me and tt.get("p_upper") is not None:
                ok = pval_str_close(me["p_upper"], tt["p_upper"])
                rows.append(("%s %s %s p_upper" % (name, dname, t), exact.fmt(me["p_upper"]), tt["p_upper"], "ok" if ok else "DIFF"))
                if not ok:
                    mism.append(("%s %s %s p_upper" % (name, dname, t), exact.fmt(me["p_upper"]), tt["p_upper"]))
            if "law" in th[dname]:
                pass
        tl = th[dname].get("law", "")
        cmp("%s %s law" % (name, dname), res[dname]["law"], tl.split(" ")[0] if tl else None)
    if th.get("mutual_closest"):
        cmp("%s mutual" % name, res["mutual"], th["mutual_closest"]["num"])
    for t in TAUS:
        ps = th.get("pooled_share_" + t)
        if ps:
            cmp("%s pooled %s" % (name, t), res["pooled"][t], [ps["num"], ps["den"]])

# within-layer
within = {}
for nm in ["py_1k__py", "py_8k__py", "py_32k__py", "py_s1__py"]:
    p = os.path.join(ROOT, "out/within_" + nm + ".json")
    if not os.path.exists(p):
        continue
    w = J(p)
    layers = [(l["N"], l["n_hist"]) for l in w["layers"]]
    e = {"F": w["same_position"], "units": w["units"], "positive": w["positive"], "ties": w["ties"],
         "null_mean": exact.same_pos_mean(layers)}
    if w["same_position"] <= 300:
        e["p"] = exact.same_pos_upper(layers, w["same_position"])
    else:
        e["bound_below_0.001"], e["bound_log10"] = exact.factorial_bound_small(len(layers), w["same_position"])
    within[nm] = e
    tp = os.path.join(RM, "out/within_layer", nm + ".json")
    if os.path.exists(tp):
        t = J(tp)
        cmp("within %s same position" % nm, e["F"], t["same_position"]["num"] if isinstance(t.get("same_position"), dict) else t.get("same_position"))
        if "null_mean" in t:
            cmp("within %s null mean" % nm, e["null_mean"], Fraction(str(t["null_mean"])))

wc = J(os.path.join(ROOT, "out/weights_check.json"))
tw = theirs_res["exploratory_post_hoc"]["weight_gate_up_sign"]
for k, v in tw.items():
    if k in wc:
        cmp("weights %s gate-up positive" % k, [wc[k]["positive"], wc[k]["units"]], [v["gate_up_inner_positive"]["num"], v["gate_up_inner_positive"]["den"]])

# ---------------- scoring by PLAN.txt rules
TH = Fraction(1, 1000)


def share(name, d="ab", t="tau_0.3"):
    e = mine_pairs[name][d][t]
    return Fraction(e["positive"], e["kept"])


def F_inside(name, d="ab", t="tau_0"):
    e = mine_pairs[name][d][t]
    lo, hi = e["F_p_upper"]
    if lo >= TH:
        return True
    if hi < TH:
        return False
    return None


score = {}
P = mine_pairs
sm = model_stats
# P1
a = share("s135__s135i") >= Fraction(95, 100)
b = Fraction(P["s135__s135i"]["ab"]["tau_0"]["F"], P["s135__s135i"]["ab"]["tau_0"]["kept"]) >= Fraction(9, 10)
score["P1"] = {"parts": [a, b], "outcome": "hit" if a and b else ("partial" if a or b else "miss")}
# P2
a = P["s135__s360"]["ab"]["tau_0.3"]["p_two"] >= TH
b = sm["s135"]["skew_pass"]; c = sm["s360"]["skew_pass"]
n = sum([a, b, c]); score["P2"] = {"parts": [a, b, c], "outcome": "hit" if n == 3 else "partial" if n == 2 else "miss"}
# P3
a = all(not sm[k]["skew_pass"] for k in ["py", "py_s1", "py_s2", "py_1k", "py_8k", "py_32k"])
seeds = ["py__py_s1", "py__py_s2", "py_s1__py_s2"]
b = all(share(s) >= Fraction(8, 10) for s in seeds)
cs = [F_inside(s) for s in seeds]
c = all(x is True for x in cs)
n = sum([a, b, c]); score["P3"] = {"parts": [a, b, c], "outcome": "hit" if n == 3 else "partial" if n == 2 else "miss"}
# P4
e1 = P["py_1k__py"]["ab"]["tau_0"]
fs = Fraction(e1["F"], e1["kept"])
a = (Fraction(8, 100) <= fs <= Fraction(35, 100)) and e1.get("F_bound_below_0.001", False)
f8 = Fraction(P["py_8k__py"]["ab"]["tau_0"]["F"], P["py_8k__py"]["ab"]["tau_0"]["kept"])
f32 = Fraction(P["py_32k__py"]["ab"]["tau_0"]["F"], P["py_32k__py"]["ab"]["tau_0"]["kept"])
b = fs < f8 < f32
score["P4"] = {"parts": [a, b], "outcome": "hit" if a and b else ("partial" if a or b else "miss"),
               "same_pos_shares": [str(fs), str(f8), str(f32)]}
# P5
a = not sm["falcon"]["skew_pass"]; b = share("py__falcon") >= Fraction(75, 100)
score["P5"] = {"parts": [a, b], "outcome": "hit" if a and b else ("partial" if a or b else "miss")}
# P6 (a) from my own laundered copy (hookcheck) and their recorded logit diff
hk = J(os.path.join(ROOT, "out/hook/hookcheck_mps.json"))
a_mine = all(ch["max_abs_logit_diff"] <= 1e-3 * ch["max_abs_logit"] for ch in hk["step4"]["chunks"])
lm = J(os.path.join(RM, "traces/s135L/meta.json") if os.path.exists(os.path.join(RM, "traces/s135L/meta.json")) else os.path.join(RM, "out/trace_meta/s135L.json"))
a_theirs = lm["laundered_max_abs_logit_diff"] <= 1e-3 * lm["reference_max_abs_logit"]
out6 = {}
for nm in ["s135__s135L", "s135__mylaund5150"]:
    b = P[nm]["ab"]["tau_0.3"]["p_two"] >= TH
    cF = F_inside(nm)
    inv_l = P[nm]["ab"]["tau_0"]["invariant"]; inv_i = P["s135__s135i"]["ab"]["tau_0"]["invariant"]
    inv_u = P["s135__s360"]["ab"]["tau_0"]["invariant"]
    d = abs(inv_l - inv_i) <= 0.05 * inv_i
    e = inv_l >= inv_u + 0.10
    aa = a_theirs if nm == "s135__s135L" else a_mine
    parts = [aa, b, cF, d, e]
    nb = sum(1 for x in parts[1:] if x is True)
    oc = "hit" if all(x is True for x in parts) else ("partial" if aa and nb >= 3 else "miss")
    out6[nm] = {"parts": parts, "outcome": oc, "F_p_bracket": [exact.fmt(v) for v in P[nm]["ab"]["tau_0"]["F_p_upper"]],
                "invariants_tau0": [inv_l, inv_i, inv_u]}
score["P6"] = out6
# P7
s7 = share("q08__q2")
score["P7"] = {"share": str(s7), "outcome": "hit" if s7 >= Fraction(85, 100) else "partial" if s7 >= Fraction(70, 100) else "miss"}
# M1
score["M1"] = {"falcon_skew_pass": sm["falcon"]["skew_pass"], "outcome": "miss" if not sm["falcon"]["skew_pass"] else "?"}
# M2
mm = [Fraction(P[s]["mutual"], P[s]["nA"]) for s in seeds]
k = sum(1 for x in mm if Fraction(3, 100) <= x <= Fraction(20, 100))
score["M2"] = {"shares": [str(x) for x in mm], "outcome": "hit" if k == 3 else "partial" if k >= 1 else "miss"}
# M3
a = Fraction(60, 100) <= f8 <= Fraction(98, 100); b = Fraction(85, 100) <= f32 <= 1
score["M3"] = {"parts": [a, b], "outcome": "hit" if a and b else ("partial" if a or b else "miss")}
# M4
s4 = share("py__falcon_gate")
score["M4"] = {"share": str(s4), "outcome": "hit" if s4 >= Fraction(75, 100) else "partial" if s4 >= Fraction(60, 100) else "miss"}
# instrument checks
sp = P["s135__s135"]["ab"]
score["self_pair"] = {"ok": all(sp[t]["positive"] == sp[t]["kept"] == P["s135__s135"]["nA"] for t in TAUS) and sp["tau_0"]["F"] == sp["tau_0"]["kept"]}
sh = P["s135__s135i_shuf"]["ab"]
score["shuffled"] = {"invariant": sh["tau_0"]["invariant"], "kept_0.3": sh["tau_0.3"]["kept"],
                     "share0": [sh["tau_0"]["positive"], sh["tau_0"]["kept"]], "p_two": exact.fmt(sh["tau_0"]["p_two"]),
                     "ok": sh["tau_0"]["invariant"] < 0.10 and sh["tau_0"]["p_two"] >= TH}


def ser(x):
    if isinstance(x, Fraction):
        return exact.fmt(x) if x.denominator > 10 ** 12 or x.numerator > 10 ** 12 else str(x)
    if isinstance(x, (list, tuple)):
        return [ser(v) for v in x]
    if isinstance(x, dict):
        return {k: ser(v) for k, v in x.items()}
    return x


out = {"pairs": ser(mine_pairs), "models": ser({k: {kk: v[kk] for kk in ("skew_pos", "skew_neg", "skew_p_two", "skew_pass", "mean_pos", "pos_on_gt90pct_words", "zero_var", "units")} for k, v in model_stats.items()}),
       "within_layer": ser(within), "score": ser(score), "comparison_rows": [list(map(str, r)) for r in rows],
       "mismatches": [list(map(str, m)) for m in mism]}
with open(os.path.join(ROOT, "out/compare.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("comparisons", len(rows), "mismatches", len(mism))
for m in mism:
    print("MISMATCH", m)
print(json.dumps(ser(score), indent=1))
