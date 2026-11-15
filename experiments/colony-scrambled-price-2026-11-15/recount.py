#!/usr/bin/env python3
"""Second count of the scrambled-price runs, written apart from count_first_choice.py.

Reads results/steps.jsonl (see extract_steps.py) and the run logs in results/.
Prints the first choice per arm, how each cell first came to run on light
(its own act, or a harness downshift when it could not pay for a step), the
charges of the heavy steps, and the failures per arm. Warm runs are left out.

Usage: python3 recount.py > results/recount.out
"""
import collections
import datetime
import glob
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
cells = collections.defaultdict(list)
for line in open(HERE / "results" / "steps.jsonl", encoding="utf-8"):
    r = json.loads(line)
    cells[(r["run"], r["kit"])].append(r)
iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%H:%M:%SZ")
print("earliest log row of any run, warm runs included:", iso(min(r["t"] for rows in cells.values() for r in rows)))
arms = collections.defaultdict(list)
for (run, kit), rows in sorted(cells.items()):
    if run[2] == "w":
        continue
    laws = next(r for r in rows if r["kind"] == "laws")
    steps = [r for r in rows if r["kind"] == "step"]
    first = next(r for r in rows if r["kind"] == "act")
    onto_light = left_heavy = acts_before = None
    acts_seen = heavy_acts = 0
    for r in rows:
        if r["kind"] == "act":
            acts_seen += 1
            heavy_acts += r["model"] == "heavy"
        if r["kind"] == "act" and r["next"] is not None and r["next"] != r["model"]:
            if r["next"] == "light" and onto_light is None:
                onto_light = "first act" if r is first else "later act"
            if r["model"] == "heavy" and left_heavy is None:
                left_heavy = "own act"
        elif r["kind"] == "downshift":
            if r["to"] == "light" and onto_light is None:
                onto_light, acts_before = "harness downshift", acts_seen
            if r["frm"] == "heavy" and left_heavy is None:
                left_heavy = "harness downshift"
    arms[run[2]].append(dict(
        run=run, kit=kit, laws=(laws["price_show"], laws["price_scramble"]), t0=rows[0]["t"], t1=rows[-1]["t"],
        first_step=first["step"], choice=first["next"], onto_light=onto_light or "never on light", left_heavy=left_heavy,
        acts_before=acts_before, heavy_acts=heavy_acts,
        models=[s["model"] for s in steps], charges=[s["charge"] for s in steps], usd=sum(s["usd"] or 0 for s in steps),
        bad=sum(r["kind"] == "bad_reply" for r in rows), died=sum(r["kind"] == "death" for r in rows)))
for arm in "TSH":
    C = arms[arm]
    print(f"\narm {arm}: cells {len(C)}, laws rows {sorted({c['laws'] for c in C})}, runs from {iso(min(c['t0'] for c in C))} to {iso(max(c['t1'] for c in C))}")
    print("  first choice:", dict(collections.Counter(c["choice"] for c in C)), "| step of the first act:", sorted({c["first_step"] for c in C}))
    print("  first choice by kit:", {k: dict(collections.Counter(c["choice"] for c in C if c["kit"] == k)) for k in sorted({c["kit"] for c in C})})
    print("  how the cell first came to run on light:", dict(collections.Counter(c["onto_light"] for c in C)))
    forced = sorted(c["acts_before"] for c in C if c["acts_before"] is not None)
    if forced:
        print(f"  acts a cell had taken before the harness moved it to light: {forced[0]} to {forced[-1]} ({len(forced)} cells)")
    print("  model of the last step:", dict(collections.Counter(c["models"][-1] for c in C)))
    print(f"  bad replies {sum(c['bad'] for c in C)}, cells with a death row {sum(c['died'] > 0 for c in C)}, recorded cost ${sum(c['usd'] for c in C):.4f}")
    rc = 0
    for p in sorted(glob.glob(str(HERE / "results" / f"sc-sc{arm}[1-4].log"))):
        rc += sum(json.loads(line.split(" ", 1)[1])["rc"] != 0 for line in open(p) if line[0] != "{")
    print(f"  cells with a non-zero exit code in the run logs: {rc}")
print("\nS cells that chose heavy: model and charge per step, and how the cell left heavy")
for c in arms["S"]:
    if "heavy" in c["models"]:
        print(f"  {c['run']} {c['kit']}: {list(zip([m[0] for m in c['models']], c['charges']))} | {c['left_heavy'] or 'did not leave heavy'} | acts taken on heavy: {c['heavy_acts']}")
