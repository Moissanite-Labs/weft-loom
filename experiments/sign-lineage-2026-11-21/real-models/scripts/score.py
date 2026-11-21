"""Score the predictions of PLAN.txt (f) from out/models/*.json and out/stats/*.json; write RESULTS.json.

Run: python -I score.py <folder>
Rates are written as numerator and denominator; p-values as strings.
"""
import json
import os
import sys
from fractions import Fraction

ROOT = sys.argv[1]


def M(k):
    p = os.path.join(ROOT, "out", "models", k + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def S(n):
    p = os.path.join(ROOT, "out", "stats", n + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def fr(r):
    return Fraction(r["num"], r["den"]) if r["den"] else None


def s(r):
    return "%d/%d" % (r["num"], r["den"])


def verdict(n_true, n_total, rule):
    return rule(n_true, n_total)


def main():
    res = {"plan_sha256": open(os.path.join(ROOT, "PLAN.sha256")).read().split()[0], "predictions": [],
           "models": {}, "pairs": {}}
    for k in ["s135", "s135i", "s360", "s135L", "py", "py_s1", "py_s2", "py_1k", "py_8k", "py_32k", "falcon",
              "falcon_gate", "q08", "q2"]:
        m = M(k)
        if m:
            res["models"][k] = {"skew_positive": m["skew_positive"], "skew_p_two": m["skew_p_two"],
                                "skew_test": m["skew_test"], "mean_positive": m["mean_positive"],
                                "pos_on_gt90pct_words": m["pos_on_gt90pct_words"], "zero_var": str(m["zero_var"])}
    names = ["s135__s135i", "s135__s360", "s135__s135L", "py__py_s1", "py__py_s2", "py_s1__py_s2", "py_1k__py",
             "py_8k__py", "py_32k__py", "py__falcon", "py__falcon_gate", "s135__s135", "s135__s135i_shuf",
             "q08__q2"]
    for n in names:
        st = S(n)
        if not st:
            continue
        e = {"mutual_closest": st["mutual_closest"]}
        for d in ("ab", "ba"):
            dd = st[d]
            e[d] = {"source": dd["source"], "target": dd["target"], "law": dd["law"]}
            for t in ("tau_0", "tau_0.3", "tau_0.5"):
                x = dd[t]
                y = {"share": x["share"], "matched_same_layer": x["matched_same_layer"],
                     "invariant_mean_max_abs_r": "%.4f" % x["invariant_mean_max_abs_r"]
                     if x["invariant_mean_max_abs_r"] is not None else "none"}
                for kk in ("p_upper", "p_two", "same_position", "same_position_null_mean",
                           "same_position_null_mean_exact", "same_position_p_upper",
                           "same_position_p_upper_bracket", "same_position_p_upper_bound", "clusters",
                           "kappa_num_den", "hoeffding_two"):
                    if kk in x:
                        y[kk] = x[kk] if not isinstance(x[kk], float) else "%.6e" % x[kk]
                for kk in ("inside_999_band", "same_position_inside_null", "p_exact"):
                    if kk in x:
                        y[kk] = str(x[kk])
                e[d][t] = y
        for t in ("0", "0.3", "0.5"):
            e["pooled_share_tau_" + t] = st["pooled_share_tau_" + t]
        res["pairs"][n] = e
    P = res["predictions"]

    def add(pid, text, observed, outcome):
        P.append({"id": pid, "prediction": text, "observed": observed, "outcome": outcome})

    def two_of(conds, hit_all=True):
        k = sum(1 for c in conds if c)
        return k

    # P1
    st = S("s135__s135i")
    if st:
        a = st["ab"]["tau_0.3"]; sp = st["ab"]["tau_0"]["same_position"]
        c1 = fr(a["share"]) >= Fraction(95, 100); c2 = fr(sp) >= Fraction(90, 100)
        k = c1 + c2
        add("P1", "SmolLM2-135M -> Instruct: share(0.3) >= 0.95 and same position >= 0.90",
            "share %s, same position %s" % (s(a["share"]), s(sp)), ["miss", "partial", "hit"][k])
    # P2
    st = S("s135__s360")
    if st:
        a = st["ab"]["tau_0.3"]
        c = [a.get("inside_999_band") is True, M("s135")["skew_test"] == "pass", M("s360")["skew_test"] == "pass"]
        k = sum(c)
        add("P2", "135M -> 360M: share(0.3) inside binomial 99.9% band; both pass skew test",
            "share %s, p_two %s; skew 135M %s (%s), 360M %s (%s)" % (
                s(a["share"]), a.get("p_two"), M("s135")["skew_test"], M("s135")["skew_p_two"],
                M("s360")["skew_test"], M("s360")["skew_p_two"]),
            "hit" if k == 3 else ("partial" if k == 2 else "miss"))
    # P3
    pys = ["py", "py_s1", "py_s2", "py_1k", "py_8k", "py_32k"]
    if all(M(k) for k in pys) and all(S(n) for n in ["py__py_s1", "py__py_s2", "py_s1__py_s2"]):
        ca = all(M(k)["skew_test"] == "fail" for k in pys)
        seeds = [S(n) for n in ["py__py_s1", "py__py_s2", "py_s1__py_s2"]]
        cb = all(fr(x["ab"]["tau_0.3"]["share"]) >= Fraction(8, 10) for x in seeds)
        cc = all(x["ab"]["tau_0"].get("same_position_inside_null") is True for x in seeds)
        k = ca + cb + cc
        obs = "skew: " + ", ".join("%s %s %s" % (kk, M(kk)["skew_test"], s(M(kk)["skew_positive"])) for kk in pys)
        obs += "; seed shares(0.3): " + ", ".join(s(x["ab"]["tau_0.3"]["share"]) for x in seeds)
        obs += "; same position(0): " + ", ".join("%s (null mean %s, inside %s)" % (
            s(x["ab"]["tau_0"]["same_position"]), x["ab"]["tau_0"]["same_position_null_mean"],
            x["ab"]["tau_0"].get("same_position_inside_null")) for x in seeds)
        add("P3", "all Pythia fail skew; seed shares(0.3) >= 0.80; seed same-position inside null", obs,
            "hit" if k == 3 else ("partial" if k == 2 else "miss"))
        # M2
        mut = [x["mutual_closest"] for x in seeds]
        km = sum(Fraction(3, 100) <= fr(x) <= Fraction(20, 100) for x in mut)
        add("M2 (mine)", "Pythia seed pairs mutual-closest share in [0.03, 0.20]", ", ".join(s(x) for x in mut),
            "hit" if km == 3 else ("partial" if km else "miss"))
    # P4, M3
    ck = [S(n) for n in ["py_1k__py", "py_8k__py", "py_32k__py"]]
    if all(ck):
        sp = [x["ab"]["tau_0"]["same_position"] for x in ck]
        pu = ck[0]["ab"]["tau_0"]
        null_reject = pu.get("same_position_inside_null") is False
        ca = Fraction(8, 100) <= fr(sp[0]) <= Fraction(35, 100) and null_reject
        cb = fr(sp[0]) < fr(sp[1]) < fr(sp[2])
        p_str = pu.get("same_position_p_upper") or pu.get("same_position_p_upper_bound") or str(
            pu.get("same_position_p_upper_bracket"))
        add("P4", "step1000 -> main same position in [0.08, 0.35], null p < 0.001; rises 1k < 8k < 32k",
            "same position 1k %s (null mean %s, p %s), 8k %s, 32k %s" % (
                s(sp[0]), pu["same_position_null_mean"], p_str, s(sp[1]), s(sp[2])),
            ["miss", "partial", "hit"][ca + cb])
        c1 = Fraction(60, 100) <= fr(sp[1]) <= Fraction(98, 100)
        c2 = Fraction(85, 100) <= fr(sp[2]) <= 1
        add("M3 (mine)", "same position 8k -> main in [0.60, 0.98], 32k -> main in [0.85, 1.00]",
            "8k %s, 32k %s" % (s(sp[1]), s(sp[2])), ["miss", "partial", "hit"][c1 + c2])
    # P5, M1, M4
    st = S("py__falcon")
    if st and M("falcon"):
        f = M("falcon")
        a = st["ab"]["tau_0.3"]; b = st["ba"]["tau_0.3"]
        ca = f["skew_test"] == "fail"; cb = fr(a["share"]) >= Fraction(75, 100)
        add("P5", "Falcon fails skew test; pythia -> Falcon share(0.3) >= 0.75",
            "Falcon skew %s %s (p_two %s); pythia -> Falcon share %s; Falcon -> pythia share %s" % (
                f["skew_test"], s(f["skew_positive"]), f["skew_p_two"], s(a["share"]), s(b["share"])),
            ["miss", "partial", "hit"][ca + cb])
        passes = f["skew_test"] == "pass"
        ia = a.get("inside_999_band"); ib = b.get("inside_999_band")
        if not passes:
            out = "miss"
        else:
            out = "hit" if (ia is True or ia is None) and ib is True else "partial"
        add("M1 (mine)", "Falcon passes skew; pythia -> Falcon share(0.3) inside cluster band; Falcon -> pythia "
            "inside binomial band", "Falcon %s; ab law %s inside %s (p_two %s, hoeffding %s); ba law %s inside %s "
            "(p_two %s)" % (f["skew_test"], st["ab"]["law"], ia, a.get("p_two"), a.get("hoeffding_two"),
                            st["ba"]["law"], ib, b.get("p_two")), out)
    st = S("py__falcon_gate")
    if st:
        a = st["ab"]["tau_0.3"]
        v = fr(a["share"])
        add("M4 (mine)", "pythia -> Falcon gate-only trace share(0.3) >= 0.75", s(a["share"]),
            "hit" if v >= Fraction(75, 100) else ("partial" if v >= Fraction(60, 100) else "miss"))
    # P6
    st = S("s135__s135L"); base = S("s135__s135i"); unrel = S("s135__s360")
    if st and base and unrel:
        mp = os.path.join(ROOT, "traces", "s135L", "meta.json")
        if not os.path.exists(mp):  # published record: trace metadata copied to out/trace_meta
            mp = os.path.join(ROOT, "out", "trace_meta", "s135L.json")
        with open(mp) as fh:
            lm = json.load(fh)
        ca = lm["laundered_max_abs_logit_diff"] <= 1e-3 * lm["reference_max_abs_logit"]
        a = st["ab"]["tau_0.3"]
        cb = a.get("inside_999_band") is True
        cc = st["ab"]["tau_0"].get("same_position_inside_null") is True
        inv = st["ab"]["tau_0"]["invariant_mean_max_abs_r"]
        inv_b = base["ab"]["tau_0"]["invariant_mean_max_abs_r"]
        inv_u = unrel["ab"]["tau_0"]["invariant_mean_max_abs_r"]
        cd = abs(inv - inv_b) <= 0.05 * inv_b
        ce = inv >= inv_u + 0.10
        k = cb + cc + cd + ce
        out = "hit" if ca and k == 4 else ("partial" if ca and k >= 3 else "miss")
        add("P6", "laundered: logits equal; share inside band; same position inside null; invariant within 5% of "
            "Instruct's, >= 0.10 above 360M's",
            "max logit diff %.3e (max |logit| %.2f); share %s p_two %s; same position %s (null mean %s, p %s); "
            "invariant %.4f vs Instruct %.4f vs 360M %.4f" % (
                lm["laundered_max_abs_logit_diff"], lm["reference_max_abs_logit"], s(a["share"]), a.get("p_two"),
                s(st["ab"]["tau_0"]["same_position"]), st["ab"]["tau_0"]["same_position_null_mean"],
                st["ab"]["tau_0"].get("same_position_p_upper") or st["ab"]["tau_0"].get(
                    "same_position_p_upper_bracket"), inv, inv_b, inv_u), out)
    st = S("q08__q2")
    if st:
        v = fr(st["ab"]["tau_0.3"]["share"])
        add("P7", "Qwen3.5-0.8B -> 2B share(0.3) >= 0.85", s(st["ab"]["tau_0.3"]["share"]),
            "hit" if v >= Fraction(85, 100) else ("partial" if v >= Fraction(70, 100) else "miss"))
    else:
        add("P7", "Qwen3.5-0.8B -> 2B share(0.3) >= 0.85", "not run", "not_run")
    # instrument checks
    chk = {}
    st = S("s135__s135")
    if st:
        a = st["ab"]
        chk["self_pair"] = {"share_tau0": a["tau_0"]["share"], "same_position": a["tau_0"]["same_position"],
                            "ok": str(all(fr(a[t]["share"]) == 1 for t in ("tau_0", "tau_0.3", "tau_0.5")) and
                                      fr(a["tau_0"]["same_position"]) == 1)}
    st = S("s135__s135i_shuf")
    if st:
        a = st["ab"]
        inv = a["tau_0"]["invariant_mean_max_abs_r"]
        chk["shuffled_words"] = {"share_tau0": a["tau_0"]["share"], "p_two": a["tau_0"].get("p_two"),
                                 "kept_at_0.3": str(a["tau_0.3"]["share"]["den"]),
                                 "invariant": "%.4f" % inv,
                                 "ok": str(inv < 0.10 and a["tau_0"].get("inside_999_band") is True)}
    res["instrument_checks"] = chk
    # exploratory, post hoc (not in the plan)
    ex = {}
    for n in ("py__s135", "falcon__s135"):
        st = S(n)
        if st:
            ex[n] = {}
            for d in ("ab", "ba"):
                dd = st[d]
                ex[n][d] = {"source": dd["source"], "target": dd["target"], "law": dd["law"]}
                for t in ("tau_0", "tau_0.3", "tau_0.5"):
                    x = dd[t]
                    y = {"share": x["share"]}
                    for kk in ("p_two", "clusters", "kappa_num_den"):
                        if kk in x:
                            y[kk] = x[kk]
                    if "inside_999_band" in x:
                        y["inside_999_band"] = str(x["inside_999_band"])
                    ex[n][d][t] = y
    wd = os.path.join(ROOT, "out", "within_layer")
    if os.path.isdir(wd):
        for f in sorted(os.listdir(wd)):
            w = json.load(open(os.path.join(wd, f)))
            ex["within_layer__" + f[:-5]] = {k: v for k, v in w.items() if k != "per_layer"}
    wp = os.path.join(ROOT, "out", "weights", "weight_lean.json")
    if os.path.exists(wp):
        w = json.load(open(wp))
        ex["weight_gate_up_sign"] = {k: {kk: vv for kk, vv in v.items() if kk != "per_layer"} for k, v in w.items()}
    res["exploratory_post_hoc"] = ex
    json.dump(res, open(os.path.join(ROOT, "RESULTS.json"), "w"), indent=1)
    for p in P:
        print(p["id"], p["outcome"], "|", p["observed"])
    print(json.dumps(chk))


if __name__ == "__main__":
    main()
