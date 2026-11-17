#!/usr/bin/env python3
"""Descriptions written after the runs were seen. Nothing here was preregistered.

This file was written when replicate 0 had finished and the other three had not.

    python3 explore.py            # reads results/runs/*/log.jsonl, writes results/explore.md

It asks three things the planned tables do not: how much of the gain the first build of
each slot brought, what builders did once the scoreboard showed a high score, and what each
arm cost. Standard library only.
"""

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = ["twin-free-rival", "twin-free-collective", "twin-stack-collective", "solo-pair",
        "twin-fixed-builder"]
HIGH = 0.95


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results" / "runs"
    runs = []
    for d in sorted(root.iterdir()):
        if not (d / "log.jsonl").exists():
            continue
        rows = [json.loads(x) for x in (d / "log.jsonl").read_text().splitlines() if x.strip()]
        if any(r["kind"] == "end" for r in rows):
            runs.append(rows)
    out = ["# Descriptions written after the runs were seen (explore.py)", "",
           "Nothing in this file was preregistered.", ""]

    # 1. the first gated build of each slot against all later ones
    out += ["## Where the gain came from", "",
            "For every candidate that reached the paired benchmark: the old harness's score and the candidate's, on the same 9 fresh tasks. "
            "\"First\" is the first such candidate for a slot in a run, \"later\" is every one after it.", "",
            "| Arm | First: candidates | old mean | new mean | Later: candidates | old mean | new mean |", "|---|---|---|---|---|---|---|"]
    pooled = {"first": [], "later": []}
    for arm in ARMS:
        first, later = [], []
        for rows in runs:
            if rows[0]["arm"] != arm:
                continue
            seen = set()
            for t in (r for r in rows if r["kind"] == "turn"):
                if t.get("cand") is None:
                    continue
                (later if t["target"] in seen else first).append((t["inc"], t["cand"]))
                seen.add(t["target"])
        pooled["first"] += first
        pooled["later"] += later
        f = lambda xs, i: f"{statistics.mean(x[i] for x in xs):.3f}" if xs else "-"
        out.append(f"| {arm} | {len(first)} | {f(first, 0)} | {f(first, 1)} | {len(later)} | {f(later, 0)} | {f(later, 1)} |")
    f = lambda xs, i: f"{statistics.mean(x[i] for x in xs):.3f}" if xs else "-"
    out += [f"| all arms | {len(pooled['first'])} | {f(pooled['first'], 0)} | {f(pooled['first'], 1)} | "
            f"{len(pooled['later'])} | {f(pooled['later'], 0)} | {f(pooled['later'], 1)} |", ""]

    # 2. what a builder did when the target's scoreboard value was already high
    out += ["## What builders did at a high score", "",
            f"Build turns where the scoreboard showed the target's harness at {HIGH} or more, and what the builder did.", "",
            "| Arm | Such turns | Made an edit | Edit kept | Edit discarded | No change | Mean model calls used |", "|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        n = ed = kept = disc = noop = 0
        calls = []
        for rows in runs:
            if rows[0]["arm"] != arm:
                continue
            score = {r["slot"]: r["report"]["mean"] for r in rows if r["kind"] == "baseline"}
            for t in (r for r in rows if r["kind"] == "turn"):
                if score[t["target"]] >= HIGH:
                    n += 1
                    ed += bool(t["edited"])
                    kept += t["outcome"] == "commit" and bool(t["edited"])
                    disc += t["outcome"] in ("regress", "boot_fail", "invalid")
                    noop += t["outcome"] == "noop"
                    calls.append(t["build_calls"])
                if t["outcome"] == "commit":
                    score[t["target"]] = t["cand"]
                elif t["outcome"] == "regress":
                    score[t["target"]] = t["inc"]
        out.append(f"| {arm} | {n} | {ed} | {kept} | {disc} | {noop} | {statistics.mean(calls):.1f} |" if n else f"| {arm} | 0 | - | - | - | - | - |")
    out.append("")

    # 3. cost
    out += ["## Cost by arm", "", "| Arm | Runs | Dollars per run | Model calls per run | Build calls per turn | Minutes per run |", "|---|---|---|---|---|---|"]
    for arm in ARMS:
        rs = [rows for rows in runs if rows[0]["arm"] == arm]
        if not rs:
            continue
        ends = [next(r for r in rows if r["kind"] == "end") for rows in rs]
        bc = [t["build_calls"] for rows in rs for t in rows if t["kind"] == "turn"]
        out.append(f"| {arm} | {len(rs)} | {statistics.mean(e['usd'] for e in ends):.2f} | {statistics.mean(e['calls'] for e in ends):.0f} | "
                   f"{statistics.mean(bc):.1f} | {statistics.mean(e['wall_s'] for e in ends) / 60:.0f} |")
    out.append("")
    (HERE / "results" / "explore.md").write_text("\n".join(out))
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
