#!/usr/bin/env python3
"""The cost figures of block2/PLAN.md, computed from the pilot's committed logs.

    python3 -I -B block2/costs.py > block2/costs.out

List prices as the pilot's ledger recorded them. An assay's cost is its build turn plus the
two benchmarks of its gate (the boot check's few calls are not in the row and are left out).
A run's cost is the total in its end row. Part B's build-gate overhead is an estimate: each
gate adds two build probes, each a build turn and one benchmark of its candidate, plus one
benchmark of the seed, priced at the pilot's mean assay parts.
"""
import glob
import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
assays = [json.loads(line) for f in sorted(glob.glob(str(HERE / "results" / "assay-*of4.jsonl"))) for line in open(f)]
parts = [(a.get("build_usd", 0.0), (a.get("inc_report") or {}).get("usd", 0.0), (a.get("cand_report") or {}).get("usd", 0.0))
         for a in assays]
per_assay = [sum(p) for p in parts]
build = st.mean(p[0] for p in parts)
bench = st.mean(x for p in parts for x in p[1:] if x)
runs = []
for d in sorted((HERE / "results" / "runs").iterdir()):
    end = [json.loads(line) for line in open(d / "log.jsonl") if '"kind": "end"' in line]
    runs.append(end[-1]["usd"])
mean_assay, mean_run = st.mean(per_assay), st.mean(runs)
print(f"pilot assays: {len(per_assay)}, mean {mean_assay:.4f}, total {sum(per_assay):.3f}")
print(f"  of which: build turn mean {build:.4f}, one benchmark mean {bench:.4f}")
print(f"pilot fault-free runs: {len(runs)}, mean {mean_run:.4f}, total {sum(runs):.3f}")
part_a = 19 * 2 * 3 + 12
print(f"part A: {part_a} assays x {mean_assay:.4f} = {part_a * mean_assay:.2f}")
gate_extra = 2 * (build + bench) + bench
run_b = mean_run + 6 * gate_extra
b_plain, b_gate, b_assays = 18 * mean_run, 6 * run_b, 24 * 6 * mean_assay
print(f"part B: 18 plain runs {b_plain:.2f}; build-gate extra per gate {gate_extra:.4f}, per run {run_b:.4f},"
      f" 6 runs {b_gate:.2f}; 144 assays {b_assays:.2f}; total {b_plain + b_gate + b_assays:.2f}")
