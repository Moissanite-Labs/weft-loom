"""Identical puzzles across and within the sets of the plan, by exact count.

The record proves that the seed ranges of its sets are disjoint. Distinct
seeds can still generate the same puzzle, so this script builds every episode
of every set of the full plan and of the pilot from its seed, with the
record's own builder, and counts exact duplicates.

Sets: train, heldout1 and heldout2 (the full plan), pilot_train and pilot_eval
(the pilot). The full plan is the one pilot_cli.py projects the time for
(2048 training examples, 2 seeds, the default cap).

Canonical forms. Both are the exact text a model is shown, so nothing a model
could see is ignored:
  puzzle   the first user message: the variable count, the goal line and every
           constraint with its name, its two variables and its bound
  episode  the puzzle, the failed attempt (one line per variable) and the
           canonical repair that is the training target
Tier and seed are not part of either form: they are not shown to the model.
A pair of episodes from different tiers cannot match, because the variable
count is part of the puzzle text.

Counts, all integers:
  within a set   episodes (n), distinct forms, repeated episodes (n minus
                 distinct), at both levels
  across a pair  distinct forms present in both sets, episodes of the first set
                 whose form is in the second, episodes of the second set whose
                 form is in the first, at both levels

    python3 -I -B checks/split_overlap.py
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cost  # noqa: E402
import episodes as ep_mod  # noqa: E402
import evaluate  # noqa: E402

FULL_EXAMPLES, FULL_SEEDS = 2048, 2     # as in pilot_cli.py
SET_NAMES = ("train", "heldout1", "heldout2", "pilot_train", "pilot_eval")
LEVELS = ("puzzle", "episode")


def build_sets(cap=None):
    """{name: EpisodeSet}, built with the record's own builder and plan offsets."""
    cap = evaluate.DEFAULT_CAP if cap is None else cap
    full, pilot = cost.full_plan(FULL_EXAMPLES, FULL_SEEDS, cap), cost.pilot_plan(cap)
    return {
        "train": ep_mod.build_set("train", full.train_counts, full.train_offset),
        "heldout1": ep_mod.build_set("heldout1", full.eval1_counts, full.eval1_offset),
        "heldout2": ep_mod.build_set("heldout2", full.eval2_counts),
        "pilot_train": ep_mod.build_set("train", pilot.train_counts, pilot.train_offset),
        "pilot_eval": ep_mod.build_set("train", pilot.eval1_counts, pilot.eval1_offset),
    }


def forms(ep):
    """(puzzle form, episode form) of one episode: the text the model is shown."""
    r = ep_mod.render(ep, "A")
    puzzle = r.messages[0]["content"]
    return puzzle, (puzzle, r.attempt_text, r.target_text)


def keys_by_level(epset):
    """{level: [form of each episode, in order]}"""
    rows = [forms(ep) for ep in epset.episodes]
    return {"puzzle": [p for p, _e in rows], "episode": [e for _p, e in rows]}


def tally(sets):
    """Exact counts for the given EpisodeSets: (within, across).
    within[name][level] = (n, distinct)
    across[(a, b)][level] = (shared distinct forms, episodes of a in b, episodes of b in a)"""
    keys = {name: keys_by_level(s) for name, s in sets.items()}
    within = {name: {lv: (len(k[lv]), len(set(k[lv]))) for lv in LEVELS} for name, k in keys.items()}
    across = {}
    names = list(sets)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            across[(a, b)] = {}
            for lv in LEVELS:
                ca, cb = Counter(keys[a][lv]), Counter(keys[b][lv])
                shared = set(ca) & set(cb)
                across[(a, b)][lv] = (len(shared), sum(ca[k] for k in shared), sum(cb[k] for k in shared))
    return within, across


def render_report(within, across):
    lines = []
    for name in within:
        for lv in LEVELS:
            n, distinct = within[name][lv]
            lines.append("within %-12s %-8s episodes %5d distinct %5d repeated %5d" % (name, lv, n, distinct, n - distinct))
    for (a, b), per in across.items():
        for lv in LEVELS:
            shared, in_a, in_b = per[lv]
            lines.append("across %-12s %-12s %-8s shared_forms %5d episodes_of_first %5d episodes_of_second %5d"
                         % (a, b, lv, shared, in_a, in_b))
    return lines


def train_vs_heldout(across):
    """Total episodes of heldout1 and heldout2 whose puzzle is also a training puzzle."""
    return {h: across[("train", h)]["puzzle"][2] for h in ("heldout1", "heldout2")}


def main():
    sets = build_sets()
    within, across = tally(sets)
    for line in render_report(within, across):
        print(line)
    tv = train_vs_heldout(across)
    sizes = {n: len(s) for n, s in sets.items()}
    for h in ("heldout1", "heldout2"):
        print("train_puzzle_in_%s episodes_affected %d of %d" % (h, tv[h], sizes[h]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
