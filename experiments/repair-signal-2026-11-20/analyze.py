"""Read a log, print per-arm results and the preregistered comparisons.

Everything is computed per (model, tier). Nothing is pooled across models or
tiers. The decision rule is the one written in PREREG.md.
"""
import json

import runner
import stats

ALPHA = 0.025          # one-sided, per tier (0.05 split over two tiers)
MIN_DISCORDANT = 10    # fewer discordant pairs than this: not informative
EDGE = 0.05            # every arm at or below EDGE, or at or above 1-EDGE: floor or ceiling


def load_units(path):
    return [r for r in runner.read_log(path) if r.get("type") == "unit"]


def table(units):
    """{(model, tier): {arm: {instance: unit}}}"""
    t = {}
    for u in units:
        t.setdefault((u["model"], u["tier"]), {}).setdefault(u["arm"], {})[u["instance"]] = u
    return t


def compare(by_arm, first, second, k, alternative="greater"):
    """Is `first` better than `second`? Paired on instances present in both."""
    ids = sorted(set(by_arm[first]) & set(by_arm[second]))
    a, b = by_arm[first], by_arm[second]
    wins = sum(1 for i in ids if a[i]["passed"] and not b[i]["passed"])
    losses = sum(1 for i in ids if b[i]["passed"] and not a[i]["passed"])
    rd = lambda u: u["pass_round"] if u["passed"] else k + 1
    diffs = [rd(b[i]) - rd(a[i]) for i in ids]
    return {"first": first, "second": second, "pairs": len(ids), "first_only": wins,
            "second_only": losses,
            "p_pass_sign": stats.sign_test(wins, losses, alternative),
            "p_reverse": stats.sign_test(losses, wins, "greater"),
            "p_rounds_signflip": stats.signflip_test(diffs)}


def arm_summary(d):
    us = list(d.values())
    n = len(us)
    passed = [u for u in us if u["passed"]]
    tr = sum(u["transitions"] for u in us)
    return {"n": n, "pass": len(passed), "pass_rate": len(passed) / n if n else None,
            "mean_pass_round": (sum(u["pass_round"] for u in passed) / len(passed)) if passed else None,
            "repeat_rate": (sum(u["stagnant"] for u in us) / tr) if tr else None,
            "unparsable_rate": sum(u["unparsable_rounds"] for u in us) / max(1, sum(u["rounds_used"] for u in us))}


def decide(arms, primary):
    """The PREREG.md rule for one model and tier."""
    rates = [a["pass_rate"] for a in arms.values() if a["pass_rate"] is not None]
    if not rates or primary["pairs"] == 0:
        return "no_data"
    if all(r <= EDGE for r in rates) or all(r >= 1 - EDGE for r in rates):
        return "floor_or_ceiling"
    if primary["first_only"] + primary["second_only"] < MIN_DISCORDANT:
        return "too_few_discordant_pairs"
    if primary["p_pass_sign"] <= ALPHA:
        return "supports"
    if primary["p_reverse"] <= ALPHA or primary["first_only"] <= primary["second_only"]:
        return "against"
    return "inconclusive"


def overall(verdicts):
    """Combine the tier verdicts of one model."""
    vs = list(verdicts.values())
    if "supports" in vs and "against" not in vs:
        return "supports"
    if vs and all(v == "against" for v in vs):
        return "against"
    if "against" in vs and "supports" in vs:
        return "mixed"
    return "not_decided"


def summarize(units, k):
    out = {}
    for (model, tier), by_arm in sorted(table(units).items()):
        arms = {arm: arm_summary(d) for arm, d in sorted(by_arm.items())}
        comps = {}
        for name, (f, s) in {"primary_C_vs_B": ("C", "B"), "check_B_vs_A": ("B", "A"),
                             "check_C_vs_D": ("C", "D")}.items():
            if f in by_arm and s in by_arm:
                comps[name] = compare(by_arm, f, s, k, "greater")
        verdict = decide(arms, comps["primary_C_vs_B"]) if "primary_C_vs_B" in comps else "no_data"
        out.setdefault(model, {"tiers": {}})["tiers"][tier] = {"arms": arms, "comparisons": comps,
                                                              "verdict": verdict}
    for model, m in out.items():
        m["overall"] = overall({t: v["verdict"] for t, v in m["tiers"].items()})
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("logs", nargs="+", help="one or more JSON-lines logs from runner.py")
    ap.add_argument("--k", type=int, default=4)
    a = ap.parse_args(argv)
    units = []
    for path in a.logs:
        units += load_units(path)
    print(json.dumps(summarize(units, a.k), indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
