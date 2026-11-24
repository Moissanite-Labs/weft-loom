#!/usr/bin/env python3
"""Descriptive tables for the README. Written after the confirmatory run: it only tabulates
`data/results.json`, and none of what it prints was predicted.

    python3 describe.py data/results.json
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

NAMED = ["warm", "light", "tilt", "contrast"]


def rng(values) -> str:
    values = list(values)
    return f"{min(values):.3g} to {max(values):.3g} (median {st.median(values):.3g})"


def main() -> None:
    doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for arm in ("random", "fitted"):
        hosts = [h for h in doc["hosts"] if h["arm"] == arm]
        print(f"\n== {arm}: {len(hosts)} hosts ==")
        if arm == "fitted":
            print("fit error before:", rng(h["fit_rms_before"] for h in hosts), "| after:", rng(h["fit_rms_after"] for h in hosts))
        print("output rms:", rng(h["output_rms"] for h in hosts), "| weight length:", rng(h["weight_length"] for h in hosts))
        print("lam_max:", rng(h["geometry"]["lam_max"] for h in hosts), "| kappa:", rng(h["geometry"]["kappa"] for h in hosts))
        for n in NAMED + ["check"]:
            print(f"open share {n}:", rng(h["geometry"]["shares"][n] for h in hosts))
        print("-- first-order relative error of treadle moves (share >= 0.2), worst per host")
        for t in doc["constants"]["travels"]:
            worst = []
            for h in hosts:
                w = 0.0
                for n, share in h["geometry"]["shares"].items():
                    if share >= 0.2:
                        w = max([w] + [r["first_order_error"] for r in h["linearity"][n] if abs(abs(r["travel"]) - t) < 1e-12])
                worst.append(w)
            print(f"  travel {t}: {rng(worst)}")
        print("-- heddles: mean share of warm, light, tilt, contrast as a fraction of open")
        for count in doc["constants"]["pin_counts"]:
            pr, re, leak1, near1, near4, held_p, held_r, pinp, pinr = [], [], [], [], [], [], [], [], []
            for h in hosts:
                l = next(x for x in h["locks"] if x["pins"] == count)
                o = sum(h["geometry"]["shares"][n] for n in NAMED)
                pr.append(sum(l["shares_projected"][n] for n in NAMED) / o)
                re.append(sum(l["shares_rethreaded"][n] for n in NAMED) / o)
                pinp.append(l["pin_change_shed"] / l["pin_change_open"])
                pinr.append(l["pin_change_rethreaded"] / l["pin_change_open"])
                near1.append(l["near1_change_rethreaded"] / l["near1_change_open"])
                near4.append(l["near4_change_rethreaded"] / l["near4_change_open"])
                held_p.append(l["held_change_shed"] / l["held_change_open"])
                held_r.append(l["held_change_rethreaded"] / l["held_change_open"])
            better = sum(1 for a, b in zip(re, pr) if a > b)
            print(f"  {count:2d} pins: projected {rng(pr)} | rethreaded {rng(re)} | rethreaded higher on {better} of {len(hosts)}")
            print(f"           pin move / unpinned: projected {rng(pinp)} | rethreaded {rng(pinr)}")
            print(f"           1 cell away {rng(near1)} | 4 cells away {rng(near4)}")
            print(f"           held-out change / unpinned: projected {rng(held_p)} | rethreaded {rng(held_r)}")
        print("-- hiding: change on held-out inputs of a move of length 0.3 hidden from g x g known probes")
        for g in doc["constants"]["known_grids"]:
            rows = [next(x for x in h["hiding"] if x["known_grid"] == g) for h in hosts]
            print(f"  g={g:2d}: elsewhere {rng(r['elsewhere'] for r in rows)} | on known {rng(r['on_known'] for r in rows)} | "
                  f"fresh max / search worst {rng(r['fresh_max'] / r['worst'] for r in rows)} | search worst {rng(r['worst'] for r in rows)}")
        print("-- ball: breaking radius along the top shaft", rng(h["ball"]["top_shaft_breaking_radius"] for h in hosts),
              "| tau/sqrt(lam_max)", rng(h["ball"]["first_order_radius"] for h in hosts),
              "| proved radius", rng(h["ball"]["certified_radius"] for h in hosts))
        print("   smallest worst-input change among random moves at the gate's radius:", rng(min(h["ball"]["random_at_radius_worst"]) for h in hosts))
        print("   bound checks:", sum(h["bound"]["checks"] for h in hosts), "violations:", sum(h["bound"]["violations"] for h in hosts))
        bands = [("below 0.3", 0.0, 0.3), ("0.3 to 0.7", 0.3, 0.7), ("0.7 to 1.0", 0.7, 1.0), ("1.0 to 1.5", 1.0, 1.5), ("1.5 and up", 1.5, 1e9)]
        print("-- forecast: snaps by tension band, all hosts pooled")
        for label, lo, hi in bands:
            picks = [f for h in hosts for f in h["forecast"] if lo <= f["tension"] < hi]
            print(f"  {label}: {sum(f['snap'] for f in picks)} of {len(picks)}")
        ratios = [f["worst"] / (f["tension"] * doc["constants"]["tau"]) for h in hosts for f in h["forecast"]]
        print("   search worst / forecast worst over all picks:", rng(ratios))
        odd = [(h["seed"], round(f["tension"], 3), round(f["worst"], 3)) for h in hosts for f in h["forecast"] if (f["tension"] >= 1.0) != f["snap"] and not (0.7 <= f["tension"] < 1.0)]
        print("   picks outside 0.7 to 1.0 whose outcome the forecast missed (seed, tension, worst):", odd)


if __name__ == "__main__":
    main()
