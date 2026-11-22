"""How often rule 2 of the canonical repair (the search) has tied answers, by exact enumeration.

Rule 2 tries the one- and two-variable moves in the order of episodes.search_order
(smallest total size first, then fewer variables, then variable and step) and
takes the first that passes. This script counts, in the training set and in
both held-out sets, the episodes where rule 2 is the rule that fires and
another passing move of the same total size exists, and how many of those
differ in the repaired answer (two moves can give one answer).

    python3 -I -B checks/rule2_ties.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cost  # noqa: E402
import episodes as ep_mod  # noqa: E402


def passing_moves(R, inst, attempt):
    vios = R.check(inst, list(attempt))
    moves = sorted({(var, delta) for v in vios for var, delta in ((v.u, -v.excess), (v.w, v.excess))},
                   key=lambda m: (abs(m[1]), m[0], m[1]))
    out = []
    for move in ep_mod.search_order(moves):
        cand = list(attempt)
        for var, delta in move:
            cand[var] = cand[var] + delta
        if not R.check(inst, cand):
            out.append((sum(abs(d) for _v, d in move), len(move), tuple(cand)))
    return out


def main():
    R = ep_mod.rsig()
    plan = cost.full_plan(2048, 2, 96)
    sets = (("training", ep_mod.build_set("train", plan.train_counts)),
            ("held-out 1", ep_mod.build_set("heldout1", plan.eval1_counts)),
            ("held-out 2", ep_mod.build_set("heldout2", plan.eval2_counts)))
    print("%-12s %9s %10s %22s %28s" % ("set", "episodes", "by search", "same-size passing move", "same size, different answer"))
    for name, epset in sets:
        fires = same_size = other_answer = 0
        for ep in epset.episodes:
            if ep.target_rule != "search":
                continue
            fires += 1
            moves = passing_moves(R, ep.instance, ep.attempt)
            first = moves[0]
            tied = [m for m in moves[1:] if m[0] == first[0]]
            same_size += bool(tied)
            other_answer += any(m[2] != first[2] for m in tied)
        print("%-12s %9d %10d %22d %28d" % (name, len(epset), fires, same_size, other_answer))
    return 0


if __name__ == "__main__":
    sys.exit(main())
