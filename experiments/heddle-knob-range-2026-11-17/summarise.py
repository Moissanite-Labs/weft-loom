#!/usr/bin/env python3
"""Read a results file from study.py and state each prediction of PREREG.md per host.

    python3 summarise.py results.json            (prints the tables)
    python3 summarise.py results.json --json summary.json

This file was written and frozen before the confirmatory run. It only tabulates: every rule
below is a prediction of PREREG.md, written as a function of one host's measurements that
returns (holds, the number that decided it).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

PASS_MARK = 11          # a prediction is confirmed in an arm when it holds on this many of 12 hosts
NAMED = ["warm", "light", "tilt", "contrast"]   # the four treadles the shafts carry; "check" is the foil


def label_factor(host: dict, travels: list[float], floor: float) -> float:
    """Worst factor between promised and measured gain, over treadles with share >= floor."""
    worst = 0.0
    for name, share in host["geometry"]["shares"].items():
        if share < floor:
            continue
        for row in host["linearity"][name]:
            if any(abs(abs(row["travel"]) - t) < 1e-12 for t in travels):
                ratio = row["ratio"]
                worst = max(worst, abs(math.log(ratio)) if ratio and ratio > 0 else math.inf)
    return math.exp(worst)


def add_error(host: dict, travels: list[float]) -> float:
    return max(a["superposition_error"] for a in host["additivity"]
               if any(abs(a["travel"] - t) < 1e-12 for t in travels))


def lock(host: dict, pins: int) -> dict:
    return next(l for l in host["locks"] if l["pins"] == pins)


def hide(host: dict, grid: int) -> dict:
    return next(h for h in host["hiding"] if h["known_grid"] == grid)


def mean_share(shares: dict) -> float:
    return sum(shares[n] for n in NAMED) / len(NAMED)


def predictions(floor: float) -> dict:
    small = [0.05, 0.1, 0.2, 0.3, 0.45, 0.6]
    return {
        "H1a label within 1.1 up to travel 0.6":
            lambda h: (label_factor(h, small, floor) <= 1.1, label_factor(h, small, floor)),
        "H1b label within 1.25 at travel 0.9":
            lambda h: (label_factor(h, [0.9], floor) <= 1.25, label_factor(h, [0.9], floor)),
        "H1c label outside 1.1 at travel 2.5":
            lambda h: (label_factor(h, [2.5], floor) > 1.1, label_factor(h, [2.5], floor)),
        "H2a two treadles add within 0.06 up to travel 0.3":
            lambda h: (add_error(h, [0.05, 0.1, 0.2, 0.3]) <= 0.06, add_error(h, [0.05, 0.1, 0.2, 0.3])),
        "H2b two treadles add within 0.2 at travel 0.9":
            lambda h: (add_error(h, [0.9]) <= 0.2, add_error(h, [0.9])),
        "H3a 4 heddles: pinned points move under 0.1 of unpinned":
            lambda h: (lock(h, 4)["pin_change_rethreaded"] / lock(h, 4)["pin_change_open"] < 0.1,
                       lock(h, 4)["pin_change_rethreaded"] / lock(h, 4)["pin_change_open"]),
        "H3b 4 heddles: points 4 cells away move under 0.6 of unpinned":
            lambda h: (lock(h, 4)["near4_change_rethreaded"] / lock(h, 4)["near4_change_open"] < 0.6,
                       lock(h, 4)["near4_change_rethreaded"] / lock(h, 4)["near4_change_open"]),
        "H3c 16 heddles: mean share under 0.7 of open":
            lambda h: (mean_share(lock(h, 16)["shares_rethreaded"]) / mean_share(h["geometry"]["shares"]) < 0.7,
                       mean_share(lock(h, 16)["shares_rethreaded"]) / mean_share(h["geometry"]["shares"])),
        "H4a hidden from 4x4 probes: 5 times more change elsewhere":
            lambda h: (hide(h, 4)["elsewhere"] / hide(h, 4)["on_known"] >= 5.0,
                       hide(h, 4)["elsewhere"] / hide(h, 4)["on_known"]),
        "H4b more known probes, less room: change elsewhere falls at every step":
            lambda h: (all(a["elsewhere"] > b["elsewhere"] for a, b in zip(h["hiding"], h["hiding"][1:])),
                       hide(h, 10)["elsewhere"] / hide(h, 3)["elsewhere"]),
        "H4c hidden from 10x10: 64 fresh probes see under 0.9 of the search's worst":
            lambda h: (hide(h, 10)["fresh_max"] / hide(h, 10)["worst"] < 0.9,
                       hide(h, 10)["fresh_max"] / hide(h, 10)["worst"]),
        "H5a worst direction at least 4 times a typical one (kappa)":
            lambda h: (h["geometry"]["kappa"] >= 4.0, h["geometry"]["kappa"]),
        "H5b all 20 random moves at the gate's radius break the claim":
            lambda h: (h["ball"]["random_at_radius_refuted"] == 20, h["ball"]["random_at_radius_refuted"]),
        "H5c proved radius 2 to 10 times under the breaking radius; bound never exceeded":
            lambda h: (2.0 <= h["ball"]["top_shaft_breaking_radius"] / h["ball"]["certified_radius"] <= 10.0
                       and h["bound"]["violations"] == 0,
                       h["ball"]["top_shaft_breaking_radius"] / h["ball"]["certified_radius"]),
        "H7a no pick with tension under 0.7 snaps":
            lambda h: (not any(f["snap"] for f in h["forecast"] if f["tension"] < 0.7),
                       sum(1 for f in h["forecast"] if f["tension"] < 0.7 and f["snap"])),
        "H7b every pick with tension 1.0 or more snaps":
            lambda h: (all(f["snap"] for f in h["forecast"] if f["tension"] >= 1.0),
                       sum(1 for f in h["forecast"] if f["tension"] >= 1.0 and not f["snap"])),
        "H7c the search's worst input is within 1.25 of the forecast":
            lambda h: (max(abs(math.log(f["worst"] / (f["tension"] * 0.5))) for f in h["forecast"]) <= math.log(1.25),
                       math.exp(max(abs(math.log(f["worst"] / (f["tension"] * 0.5))) for f in h["forecast"]))),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--json")
    args = ap.parse_args()
    doc = json.loads(Path(args.results).read_text(encoding="utf-8"))
    rules = predictions(doc["constants"]["share_floor"])
    arms = sorted({h["arm"] for h in doc["hosts"]}, key=["random", "fitted"].index)
    summary = {"results": args.results, "programs": doc["programs"], "pass_mark": PASS_MARK, "arms": {}}
    for arm in arms:
        hosts = [h for h in doc["hosts"] if h["arm"] == arm]
        print(f"\n{arm} arm, {len(hosts)} hosts (seeds {', '.join(str(h['seed']) for h in hosts)})")
        print(f"{'prediction':78s} {'holds':>7s}  {'range of the deciding number':s}")
        table = {}
        for name, rule in rules.items():
            got = [rule(h) for h in hosts]
            held = sum(1 for ok, _ in got if ok)
            values = [float(v) for _, v in got]
            mark = "" if len(hosts) < 12 else ("  confirmed" if held >= PASS_MARK else "  NOT CONFIRMED")
            print(f"{name:78s} {held:3d}/{len(hosts):<3d}  {min(values):.4g} to {max(values):.4g}{mark}")
            table[name] = {"held": held, "of": len(hosts), "min": min(values), "max": max(values),
                           "misses": [h["seed"] for h, (ok, _) in zip(hosts, got) if not ok]}
        summary["arms"][arm] = table
    if args.json:
        Path(args.json).write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
