#!/usr/bin/env python3
"""Read the run logs and write the numbers the README quotes.

    python3 analyze.py                # reads results/runs/*/log.jsonl, writes results/summary.json
                                      # and results/tables.md

Standard library only. Every figure in the README's result tables is copied from
results/tables.md, which this script writes from the logs and nothing else.
"""

from __future__ import annotations

import itertools
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = ["twin-free-rival", "twin-free-collective", "twin-stack-collective", "solo-pair",
        "twin-fixed-builder"]
VISIBLE = ("ledger", "logwin", "bugfix")
HELDOUT = ("stock", "spec")
CONTRASTS = [  # (name, arm x, arm y): reported as mean(x) - mean(y)
    ("twin minus solo", "twin-free-collective", "solo-pair"),
    ("live builder minus seed builder", "twin-free-collective", "twin-fixed-builder"),
    ("stack minus free", "twin-stack-collective", "twin-free-collective"),
    ("rival minus collective", "twin-free-rival", "twin-free-collective"),
]


def load(run_dir: Path) -> dict | None:
    rows = [json.loads(x) for x in (run_dir / "log.jsonl").read_text().splitlines() if x.strip()]
    if not any(r["kind"] == "end" for r in rows):
        return None
    start = next(r for r in rows if r["kind"] == "start")
    turns = [r for r in rows if r["kind"] == "turn"]
    exams = {r["slot"]: r for r in rows if r["kind"] == "exam"}
    base = {r["slot"]: r["report"]["mean"] for r in rows if r["kind"] == "baseline"}
    end = next(r for r in rows if r["kind"] == "end")

    def split(rep):
        vis = [e["score"] for e in rep["episodes"] if e["family"] in VISIBLE]
        held = [e["score"] for e in rep["episodes"] if e["family"] in HELDOUT]
        return (statistics.mean(vis) if vis else None, statistics.mean(held) if held else None)

    ex = {s: split(exams[s]["report"]) for s in ("A", "B")}
    outcomes = [t["outcome"] for t in turns]
    return {
        "run": start["run"], "arm": start["arm"], "rep": start["rep"],
        "seed_harness": start["seed_harness"], "baseline": base,
        "outcomes": outcomes,
        "edited": [bool(t["edited"]) for t in turns],
        "turn_scores": [(t["t"], t["target"], t.get("inc"), t.get("cand"), t["outcome"]) for t in turns],
        "exam_visible": {s: ex[s][0] for s in ex}, "exam_heldout": {s: ex[s][1] for s in ex},
        "pair_visible": statistics.mean(ex[s][0] for s in ex),
        "pair_heldout": statistics.mean(ex[s][1] for s in ex) if ex["A"][1] is not None else None,
        "final_harness": end["harness"], "twins_differ": end["harness"]["A"] != end["harness"]["B"],
        "final_bytes": {s: next((t["candidate_bytes"] for t in reversed(turns)
                                 if t["outcome"] == "commit" and t["target"] == s), None) for s in ("A", "B")},
        "usd": end["usd"], "calls": end["calls"], "wall_s": end["wall_s"],
    }


def perm_p(x: list[float], y: list[float]) -> float:
    """Exact two-sided permutation p for a difference in means."""
    obs = abs(statistics.mean(x) - statistics.mean(y))
    pool = x + y
    hits = total = 0
    for idx in itertools.combinations(range(len(pool)), len(x)):
        a = [pool[i] for i in idx]
        b = [pool[i] for i in range(len(pool)) if i not in idx]
        total += 1
        if abs(statistics.mean(a) - statistics.mean(b)) >= obs - 1e-12:
            hits += 1
    return hits / total


def fmt(v, nd=3):
    return "n/a" if v is None else f"{v:.{nd}f}"


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results" / "runs"
    runs = [r for r in (load(d) for d in sorted(root.iterdir()) if (d / "log.jsonl").exists()) if r]
    by_arm = {a: [r for r in runs if r["arm"] == a] for a in ARMS}
    seed_ref = None
    ref_path = HERE / "results" / "seed_exam.json"
    if ref_path.exists():
        seed_ref = json.loads(ref_path.read_text())
    lines = ["# Tables written by analyze.py from the run logs", ""]

    lines += ["## Runs", "", "| Run | Baseline A, B | Outcomes by turn | Exam visible A, B | Exam held-out A, B | Calls | Dollars |",
              "|---|---|---|---|---|---|---|"]
    short = {"commit": "K", "regress": "R", "boot_fail": "B", "invalid": "I", "noop": "N"}
    for r in runs:
        lines.append(f"| {r['run']} | {fmt(r['baseline']['A'])}, {fmt(r['baseline']['B'])} | "
                     f"{''.join(short[o] for o in r['outcomes'])} | "
                     f"{fmt(r['exam_visible']['A'])}, {fmt(r['exam_visible']['B'])} | "
                     f"{fmt(r['exam_heldout']['A'])}, {fmt(r['exam_heldout']['B'])} | {r['calls']} | {r['usd']:.2f} |")
    lines += ["", "K kept, R discarded for a lower score, B discarded at boot, I discarded by the surface rules, N no change.", ""]

    lines += ["## Arms", "", "| Arm | Runs | Exam visible, pair mean (each run) | Mean | Exam held-out, pair mean (each run) | Mean | Kept | Lower | Boot | Surface | No change | Builder made an edit |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    arm_stats = {}
    for a in ARMS:
        rs = by_arm[a]
        if not rs:
            continue
        vis = [r["pair_visible"] for r in rs]
        held = [r["pair_heldout"] for r in rs]
        oc = [o for r in rs for o in r["outcomes"]]
        ed = [e for r in rs for e in r["edited"]]
        arm_stats[a] = {"n": len(rs), "visible": vis, "heldout": held,
                        "visible_mean": statistics.mean(vis), "heldout_mean": statistics.mean(held),
                        "outcomes": {k: oc.count(k) for k in short}, "turns": len(oc),
                        "edited": sum(ed), "usd": sum(r["usd"] for r in rs),
                        "calls": sum(r["calls"] for r in rs),
                        "twins_differ": sum(r["twins_differ"] for r in rs)}
        s = arm_stats[a]
        lines.append(f"| {a} | {len(rs)} | {', '.join(fmt(v) for v in vis)} | {fmt(s['visible_mean'])} | "
                     f"{', '.join(fmt(v) for v in held)} | {fmt(s['heldout_mean'])} | "
                     + " | ".join(f"{s['outcomes'][k]}" for k in short)
                     + f" | {s['edited']} of {s['turns']} |")
    lines.append("")
    if seed_ref:
        lines += [f"Seed harness on the same exam, {seed_ref['repeats']} repeats: visible "
                  f"{', '.join(fmt(v) for v in seed_ref['visible'])} (mean {fmt(statistics.mean(seed_ref['visible']))}), "
                  f"held-out {', '.join(fmt(v) for v in seed_ref['heldout'])} (mean {fmt(statistics.mean(seed_ref['heldout']))}).", ""]

    lines += ["## Contrasts", "", "| Contrast | Visible: difference in means | Exact two-sided p | Held-out: difference | Exact two-sided p |",
              "|---|---|---|---|---|"]
    contrasts = {}
    for name, x, y in CONTRASTS:
        if x in arm_stats and y in arm_stats:
            dv = arm_stats[x]["visible_mean"] - arm_stats[y]["visible_mean"]
            dh = arm_stats[x]["heldout_mean"] - arm_stats[y]["heldout_mean"]
            pv = perm_p(arm_stats[x]["visible"], arm_stats[y]["visible"])
            ph = perm_p(arm_stats[x]["heldout"], arm_stats[y]["heldout"])
            contrasts[name] = {"visible": dv, "p_visible": pv, "heldout": dh, "p_heldout": ph}
            lines.append(f"| {name} | {dv:+.3f} | {pv:.3f} | {dh:+.3f} | {ph:.3f} |")
    lines.append("")

    lines += ["## Gate, turn by turn", "", "Mean over runs of the old harness's score and the candidate's score on the same fresh tasks, for turns where a benchmark ran.", "",
              "| Arm | " + " | ".join(f"t{t}" for t in range(1, 9)) + " |", "|---|" + "---|" * 8]
    for a in ARMS:
        cells = []
        for t in range(1, 9):
            pairs = [(ts[2], ts[3]) for r in by_arm[a] for ts in r["turn_scores"] if ts[0] == t and ts[2] is not None]
            cells.append("-" if not pairs else f"{statistics.mean(p[0] for p in pairs):.2f} to {statistics.mean(p[1] for p in pairs):.2f} (n={len(pairs)})")
        if by_arm[a]:
            lines.append(f"| {a} | " + " | ".join(cells) + " |")
    lines.append("")

    total = {"runs": len(runs), "usd": round(sum(r["usd"] for r in runs), 2), "calls": sum(r["calls"] for r in runs)}
    lines += [f"Totals: {total['runs']} runs, {total['calls']} model calls, {total['usd']:.2f} dollars.", ""]
    out = {"runs": runs, "arms": arm_stats, "contrasts": contrasts, "totals": total, "seed_exam": seed_ref}
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "summary.json").write_text(json.dumps(out, indent=1))
    (HERE / "results" / "tables.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
