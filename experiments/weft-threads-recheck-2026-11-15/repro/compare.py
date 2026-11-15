#!/usr/bin/env python3
"""Compare each rerun result in out/ with the committed file it reproduces.

Prints one line per file: IDENTICAL, NOISE (numbers differ by at most 1e-6 and
nothing else differs) or DIFFERENT. Timing fields are ignored. Stops with a
non-zero exit status if any file is DIFFERENT.

Usage: python3 compare.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
THREADS = EXP / "weft-threads-2026-11-15" / "probes"
E13 = EXP / "e13-geodesic-shunting-plasmid-2026-11-12"
PAIRS = [
    ("e13_certificates_fresh.json", E13 / "e13_certificates.json"),
    ("e13-wireonly-fresh.json", THREADS / "e13-wireonly.json"),
    ("hardening-results.json", THREADS / "hardening-results.json"),
    ("intersections-results.json", THREADS / "intersections-results.json"),
    ("donor-agreement-results.json", THREADS / "donor-agreement-results.json"),
    ("scale-results.json", THREADS / "scale-results.json"),
    ("tf-splice-results.json", THREADS / "tf-splice-results.json"),
    ("tf-splice2-results.json", THREADS / "tf-splice2-results.json"),
    ("tf-splice3-results.json", THREADS / "tf-splice3-results.json"),
]
TIMING = ("wall_seconds", "sec_per_seed")


def walk(a, b, path, out):
    if any(t in path for t in TIMING):
        return
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append((f"{path}/{k}", None))
            else:
                walk(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path, None))
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    elif a != b:
        num = isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool)
        out.append((path, abs(a - b) if num else None))


bad = 0
for fresh, committed in PAIRS:
    diffs = []
    walk(json.loads(committed.read_text()), json.loads((HERE / "out" / fresh).read_text()), "", diffs)
    if not diffs:
        verdict = "IDENTICAL"
    elif all(d is not None and d <= 1e-6 for _, d in diffs):
        verdict = f"NOISE ({len(diffs)} numbers differ, largest difference {max(d for _, d in diffs):.3g})"
    else:
        verdict = f"DIFFERENT ({len(diffs)} fields, first {diffs[0][0]})"
        bad += 1
    print(f"{committed.name:32s} {verdict}")
print(f"files compared: {len(PAIRS)}, different: {bad}")
if bad:
    raise SystemExit(1)
