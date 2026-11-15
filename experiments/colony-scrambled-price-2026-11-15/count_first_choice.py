#!/usr/bin/env python3
"""Count the first model choice of every cell in the scrambled-price runs.

For each run sc[TSH][1-4] under the cells exp folder, read each cell log, check
the laws row matches the arm the run name claims, and take the model named for
the next step in the cell's first act. Every cell starts on the middle model.
Also sums the dollar cost recorded in the step usage rows.

Usage: python3 count_first_choice.py [exp_folder]
"""
import collections
import glob
import json
import sys
from pathlib import Path

EXP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Work" / "razi-cells" / "exp"
ARMS = {"T": (True, False), "S": (True, True), "H": (False, False)}
by_arm = collections.defaultdict(collections.Counter)
usd_by_arm = collections.Counter()
runs_seen = collections.Counter()
for path in sorted(glob.glob(str(EXP / "sc[TSH][1-4]" / "*" / "log.jsonl"))):
    run = Path(path).parts[-3]
    arm = run[2]
    laws = first = None
    usd = 0.0
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("event") == "laws":
            laws = (d["price_show"], d.get("price_scramble", False))
        if first is None and "act" in d and "next" in d:
            first = d["next"][0]
        u = d.get("usage") or {}
        if isinstance(u.get("usd"), (int, float)):
            usd += u["usd"]
    if laws is None or first is None:
        raise SystemExit(f"FAIL: could not read {path}")
    if laws != ARMS[arm]:
        raise SystemExit(f"FAIL: {path} laws row {laws} does not match arm {arm} {ARMS[arm]}")
    by_arm[arm][first] += 1
    usd_by_arm[arm] += usd
    runs_seen[arm] += 1
for arm in "TSH":
    total = sum(by_arm[arm].values())
    print(f"arm {arm}: cells with a first act {total} (cell logs {runs_seen[arm]}), "
          f"first choice {dict(by_arm[arm])}, recorded cost ${usd_by_arm[arm]:.4f}")
print(f"total recorded cost, all counted runs: ${sum(usd_by_arm.values()):.4f}")
