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
    # 4. every fault-free run, including the four of replicate 2 that the planned analysis leaves out
    VIS, HELD = ("ledger", "logwin", "bugfix"), ("stock", "spec")

    def pair(rows, fams):
        vals = []
        for r in rows:
            if r["kind"] == "exam":
                sc = [e["score"] for e in r["report"]["episodes"] if e["family"] in fams]
                vals.append(statistics.mean(sc))
        return statistics.mean(vals)

    out += ["## Every fault-free run", "",
            "The planned analysis reads only replicates complete in all five arms. This table adds the runs it leaves out.", "",
            "| Arm | Runs | Exam visible, pair mean (each run) | Mean | Exam held-out, pair mean (each run) | Mean |", "|---|---|---|---|---|---|"]
    for arm in ARMS:
        rs = sorted((rows for rows in runs if rows[0]["arm"] == arm), key=lambda rows: rows[0]["rep"])
        v, h = [pair(rows, VIS) for rows in rs], [pair(rows, HELD) for rows in rs]
        out.append(f"| {arm} | {len(rs)} | {', '.join(f'{x:.3f}' for x in v)} | {statistics.mean(v):.3f} | "
                   f"{', '.join(f'{x:.3f}' for x in h)} | {statistics.mean(h):.3f} |")
    out.append("")

    # 5. kept candidates that carried no edit (the stack rule sends a copy through the gate)
    out += ["## Kept candidates with and without an edit", "", "| Arm | Kept | of which the builder had edited | of which a plain copy of the builder's harness |", "|---|---|---|---|"]
    for arm in ARMS:
        ts = [t for rows in runs if rows[0]["arm"] == arm for t in rows if t["kind"] == "turn" and t["outcome"] == "commit"]
        out.append(f"| {arm} | {len(ts)} | {sum(bool(t['edited']) for t in ts)} | {sum(not t['edited'] for t in ts)} |")
    out.append("")

    # 6. the same final harnesses with one model call per task
    kx = root.parent / "kexam-1.jsonl"
    if kx.exists():
        k1 = {json.loads(x)["harness"]: json.loads(x) for x in kx.read_text().splitlines() if x.strip()}
        out += ["## The final harnesses with one model call per task", "",
                "Each final harness sat the same exam again with 1 model call per task in place of 3. One sitting each.", "",
                "| Arm | Final harnesses measured | Visible at 1 call (each) | Mean | Held-out at 1 call, mean | Visible at 3 calls, mean |", "|---|---|---|---|---|---|"]
        for arm in ARMS:
            v1, h1, v3 = [], [], []
            for rows in runs:
                if rows[0]["arm"] != arm:
                    continue
                for r in rows:
                    if r["kind"] == "exam" and r["harness"] in k1:
                        v1.append(k1[r["harness"]]["visible"])
                        h1.append(k1[r["harness"]]["heldout"])
                        v3.append(statistics.mean(e["score"] for e in r["report"]["episodes"] if e["family"] in VIS))
            if v1:
                out.append(f"| {arm} | {len(v1)} | {', '.join(f'{x:.2f}' for x in v1)} | {statistics.mean(v1):.3f} | {statistics.mean(h1):.3f} | {statistics.mean(v3):.3f} |")
        seed_rows = [x for x in k1.values() if x["first_seen"] == "seed"]
        if seed_rows:
            out += ["", f"The seed harness with 1 call: visible {seed_rows[0]['visible']:.3f}, held-out {seed_rows[0]['heldout']:.3f}."]
        out.append("")
    (HERE / "results" / "explore.md").write_text("\n".join(out))
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
