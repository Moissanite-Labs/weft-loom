#!/usr/bin/env python3
"""Block 2, part A: the planned analysis of the fresh builder assays (block2/PLAN.md).

    python3 -I -B block2/analyze_a.py R2/assay2-partA-*.jsonl > block2/results_a.md
    python3 -I -B block2/analyze_a.py --pilot results/assay-*of4.jsonl     # dry run only

The unit is the pilot run. A run's value is the mean gain of every assay of its two final
harnesses. A gain is the candidate's mean minus the seed's mean on the same fresh tasks
when the candidate reached the benchmark, and 0 when it did not (no edit, invalid, or
failed to boot), as in the pilot. Contrasts are differences of arm means with an exact
two-sided permutation p over run labels. `--pilot` reads the pilot's single assays to show
that the script runs; its output is not a result of part A.
"""

import glob
import itertools
import json
import pathlib
import sys
from collections import Counter, defaultdict

FREE, SOLO, SEEDB = "twin-free-collective", "solo-pair", "twin-fixed-builder"
ARMS = ["twin-free-rival", FREE, "twin-stack-collective", SOLO, SEEDB]
ALPHA = 0.05
PLANNED_REPS = 3          # assays per slot per run in part A
PLANNED_SLOTS = ("A", "B")
# The analysable runs: those packed in the record (19 fault-free runs; the excluded stack run
# of replicate 2 and the five faulted runs of replicate 3 are not there).
RUNS = {p.name for p in (pathlib.Path(__file__).resolve().parent.parent / "results" / "runs").iterdir()}


def gain(row):
    if row.get("outcome") in ("commit", "regress"):
        return row["cand"] - row["inc"]
    return 0.0


def arm_of(run):
    return run.rsplit("-r", 1)[0]


def exact_p(a, b):
    pooled, n = a + b, len(a)
    total = sum(pooled)
    observed = abs(sum(a) / n - sum(b) / len(b))
    hits = count = 0
    for idx in itertools.combinations(range(len(pooled)), n):
        s = sum(pooled[i] for i in idx)
        hits += abs(s / n - (total - s) / len(b)) >= observed - 1e-12
        count += 1
    return hits / count


def load(paths, pilot):
    rows = []
    for pattern in paths:
        for path in sorted(glob.glob(pattern)):
            with open(path) as f:
                rows += [json.loads(line) for line in f if line.strip()]
    kind = "assay" if pilot else "assay2"
    rows = [r for r in rows if r.get("kind") == kind]
    if pilot:
        for r in rows:
            r.setdefault("rep", 0)
    return rows


def main(argv):
    pilot = argv[:1] == ["--pilot"]
    rows = load(argv[1:] if pilot else argv, pilot)
    if not rows:
        print("no assay rows found")
        return 1
    seed_rows = [r for r in rows if r.get("run") is None]
    dropped = sorted({r["run"] for r in rows if r.get("run") is not None and r["run"] not in RUNS})
    run_rows = [r for r in rows if r.get("run") in RUNS]
    # Complete repeats only: if part A was cut short, use the repeats every run finished.
    by_run_rep = defaultdict(set)
    for r in run_rows:
        by_run_rep[r["run"]].add((r["rep"], r["slot"]))
    slots = sorted({r["slot"] for r in run_rows})
    reps_done = min(sum(1 for rep in range(PLANNED_REPS) if all((rep, s) in have for s in slots))
                    for have in by_run_rep.values())
    used = [r for r in run_rows if r["rep"] < max(reps_done, 1)]
    per_run = defaultdict(list)
    outcomes = defaultdict(Counter)
    for r in used:
        per_run[r["run"]].append(gain(r))
        outcomes[arm_of(r["run"])][r.get("outcome")] += 1
    values = defaultdict(dict)
    for run, gains in per_run.items():
        values[arm_of(run)][run] = sum(gains) / len(gains)

    out = []
    if pilot:
        out += ["DRY RUN on the pilot's single assays (slot A, one each). Not a result of part A.", ""]
    out += [f"Rows: {len(run_rows)} assays of built harnesses, {len(seed_rows)} of the seed as builder."
            f" Complete repeats used: {max(reps_done, 1)} of {PLANNED_REPS}, slots {','.join(slots)}."
            + (f" Not analysed (not among the record's runs): {', '.join(dropped)}." if dropped else ""), ""]
    out += ["| Arm | Runs | Assays | Run values | Mean | No edit | Invalid or no boot |", "|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        if arm not in values:
            continue
        v = values[arm]
        c = outcomes[arm]
        out.append(f"| {arm} | {len(v)} | {sum(c.values())} | "
                   + ", ".join(f"{x:+.3f}" for _, x in sorted(v.items()))
                   + f" | {sum(v.values()) / len(v):+.3f} | {c['noop']} | {c['invalid'] + c['boot_fail']} |")
    if seed_rows:
        g = [gain(r) for r in seed_rows]
        out += ["", f"Seed harness as builder: {len(g)} assays, mean gain {sum(g) / len(g):+.3f},"
                    f" {sum(1 for r in seed_rows if r.get('outcome') == 'noop')} without an edit."]
    out += ["", "| Contrast | Difference | Exact p | Verdict |", "|---|---|---|---|"]
    verdicts = {}
    for name, (x, y) in {"A1: free minus solo": (FREE, SOLO), "A2: free minus seed builder": (FREE, SEEDB)}.items():
        if x in values and y in values:
            a, b = list(values[x].values()), list(values[y].values())
            diff = sum(a) / len(a) - sum(b) / len(b)
            p = exact_p(a, b)
            held = diff < 0 and p <= ALPHA
            verdicts[name] = held
            out.append(f"| {name} | {diff:+.3f} | {p:.4f} | {'holds' if held else 'does not hold'} |")
    if FREE in outcomes and SOLO in outcomes:
        f_rate = outcomes[FREE]["noop"] / max(1, sum(outcomes[FREE].values()))
        s_rate = outcomes[SOLO]["noop"] / max(1, sum(outcomes[SOLO].values()))
        out.append(f"| A3: no-edit rate, free against solo | {f_rate:.3f} against {s_rate:.3f} | - |"
                   f" {'holds' if f_rate > s_rate else 'does not hold'} |")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
