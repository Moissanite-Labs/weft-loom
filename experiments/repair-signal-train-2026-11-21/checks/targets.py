"""The counts in the plan's training-target and mechanism sections, by exact enumeration.

Prints, from the committed episode builder and the exact checker:
  - how many training targets each rule of the canonical repair gives
  - the mean amount shown by text C and by text E over the training set
  - on held-out set 1, by the number of variables moved to make the failed
    attempt: how many episodes the first rule alone repairs (the shared
    variable moved by the largest excess), how many the search repairs, how
    many need the planted point
  - on held-out set 1, how many episodes pass when each violated constraint's
    first-named variable is lowered by that constraint's excess (one
    subtraction per violation)

    python3 -I -B checks/targets.py
"""
import os
import sys
from collections import Counter
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cost  # noqa: E402
import episodes as ep_mod  # noqa: E402


def main():
    R = ep_mod.rsig()
    plan = cost.full_plan(2048, 2, 96)
    train = ep_mod.build_set("train", plan.train_counts)
    rules = Counter(ep.target_rule for ep in train.episodes)
    print("training episodes %d" % len(train))
    for rule in ("max-excess", "search", "planted"):
        print("train_rule_%-10s %d" % (rule, rules[rule]))
    sums = {"C": Fraction(0), "E": Fraction(0)}
    counts = {"C": 0, "E": 0}
    for ep in train.episodes:
        vios = R.check(ep.instance, list(ep.attempt))
        for arm in ("C", "E"):
            amounts = ep_mod.amounts_for(arm, vios, ep.seed, ep.tier)
            sums[arm] += sum(Fraction(x) for x in amounts)
            counts[arm] += len(amounts)
    for arm in ("C", "E"):
        print("mean_amount_%s %.4f" % (arm, float(sums[arm] / counts[arm])))

    held = ep_mod.build_set("heldout1", plan.eval1_counts)
    by_moved = Counter((len(ep.perturbation), ep.target_rule) for ep in held.episodes)
    print("held-out 1 episodes %d" % len(held))
    for moved in sorted({k[0] for k in by_moved}):
        total = sum(n for (m, _r), n in by_moved.items() if m == moved)
        print("moved_%d total %d  max-excess %d  search %d  planted %d" % (
            moved, total, by_moved[(moved, "max-excess")], by_moved[(moved, "search")], by_moved[(moved, "planted")]))
    one_subtraction = 0
    for ep in held.episodes:
        cand = list(ep.attempt)
        for v in R.check(ep.instance, list(ep.attempt)):
            cand[v.u] -= v.excess
        one_subtraction += not R.check(ep.instance, cand)
    print("one_subtraction_per_violation %d of %d" % (one_subtraction, len(held)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
