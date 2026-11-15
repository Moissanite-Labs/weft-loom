#!/usr/bin/env python3
"""Recount, apart from colony_stats.py, the first model choice of the SP3 cells.

For each SP3 run (arms a to d, four runs each, four kits per run) read the
cell's log and take the model named in its first act. Arms a and c were shown
the price list. Arms b and d were not. Every cell starts on the middle model.

Usage: python3 recount_first_choice.py     (from anywhere inside the checkout)
"""
import collections
import glob
import json
import math
from pathlib import Path

ARCHIVE = Path(__file__).resolve().parents[3] / "archive" / "razi-cells-exp-2026-11"
per_run = collections.defaultdict(lambda: [0, 0])
by_arm = collections.defaultdict(collections.Counter)
for path in sorted(glob.glob(str(ARCHIVE / "s3[abcd][1-4]" / "*" / "log.jsonl"))):
    run = Path(path).parts[-3]
    shown = first = None
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("event") == "laws":
            shown = d["price_show"]
        if first is None and "act" in d and "next" in d:
            first = d["next"][0]
    if shown is None or first is None:
        raise SystemExit(f"FAIL: could not read {path}")
    by_arm[(run[:3], shown)][first] += 1
    per_run[(shown, run)][0] += 1
    per_run[(shown, run)][1] += first == "light"
if len(per_run) != 16:
    raise SystemExit(f"FAIL: expected 16 runs, found {len(per_run)}")
for k in sorted(by_arm):
    print(f"arm {k[0]} prices_shown={k[1]}: {dict(by_arm[k])}")
light = {s: [v[1] for (sh, r), v in sorted(per_run.items()) if sh == s] for s in (True, False)}
cells = {s: sum(v[0] for (sh, r), v in per_run.items() if sh == s) for s in (True, False)}
print(f"shown: {sum(light[True])} of {cells[True]} cells chose light; per run {light[True]}")
print(f"hidden: {sum(light[False])} of {cells[False]} cells chose light; per run {light[False]}")
if min(light[True]) > max(light[False]):
    p = 2 / math.comb(16, 8)
    print(f"every shown run is above every hidden run: exact two-sided permutation p = 2 / C(16, 8) = {p:.3g}")
