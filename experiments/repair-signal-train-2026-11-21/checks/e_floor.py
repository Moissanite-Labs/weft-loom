"""The chance floor for the C adapter on text E, on held-out set 1 (1000 episodes), by exact enumeration.

Text E shows the amounts of another puzzle with the same number of violations.
An adapter trained on C that applies the largest-excess rule mechanically to
the amounts it is shown still passes some episodes on E, because an overshoot
often stays inside the constraints' slack. This script counts how often, so
that a nonzero score on E is not read as evidence that the adapter reads the
values.

The rule here is the first rule of the canonical repair (episodes.canonical_repair)
written again from its description, applied to the SHOWN amounts instead of the
true ones:
  - a variable named by every violated constraint, always in the same role
    (first-named u or second-named w), first-named before second-named, then
    the lower index
  - lower a first-named variable, raise a second-named one, by the largest shown amount
  mechanical   take the first variable in that order, with no look at the checker
  look-ahead   take the first variable in that order whose result the checker accepts

    python3 -I -B checks/e_floor.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import episodes as ep_mod  # noqa: E402


def rule_candidates(attempt, vios, amounts):
    """Candidates of the largest-excess rule in order, for the given amounts."""
    shared = set.intersection(*[{v.u, v.w} for v in vios])
    roles = {x: {"u" if v.u == x else "w" for v in vios} for x in shared}
    order = sorted((x for x in shared if len(roles[x]) == 1), key=lambda x: (roles[x] == {"w"}, x))
    top = max(amounts)
    out = []
    for x in order:
        cand = list(attempt)
        cand[x] = cand[x] + (-top if roles[x] == {"u"} else top)
        out.append(cand)
    return out


def main():
    R = ep_mod.rsig()
    h1 = ep_mod.build_set("heldout1", {"S": 500, "M": 500})
    tot = {k: 0 for k in ("episodes", "same_in_order", "same_multiset", "same_max", "amounts", "amounts_same",
                          "true_mechanical", "true_lookahead", "e_mechanical", "e_lookahead")}
    by_k = {}
    for ep in h1.episodes:
        vios = R.check(ep.instance, list(ep.attempt))
        true = [v.excess for v in vios]
        shown = ep_mod.amounts_for("E", vios, ep.seed, ep.tier)
        tot["episodes"] += 1
        tot["same_in_order"] += shown == true
        tot["same_multiset"] += sorted(shown) == sorted(true)
        tot["same_max"] += max(shown) == max(true)
        tot["amounts"] += len(true)
        tot["amounts_same"] += sum(a == b for a, b in zip(shown, true))
        for key, amounts in (("true", true), ("e", shown)):
            cands = rule_candidates(ep.attempt, vios, amounts)
            ok = [not R.check(ep.instance, c) for c in cands]
            tot[key + "_mechanical"] += bool(ok) and ok[0]
            tot[key + "_lookahead"] += any(ok)
            if key == "e":
                row = by_k.setdefault(len(vios), [0, 0])
                row[0] += 1
                row[1] += bool(ok) and ok[0]
    print("held-out set 1, %d episodes" % tot["episodes"])
    for k, v in tot.items():
        print("%-16s %d" % (k, v))
    print("by number of violations k: [episodes, the mechanical rule on E passes]")
    for k in sorted(by_k):
        print("  k=%d %s" % (k, by_k[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
