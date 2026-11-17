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
    exam_calls = statistics.mean(e["calls"] for s in ("A", "B") for e in exams[s]["report"]["episodes"])
    t1 = turns[0]
    first_gain = (t1["cand"] - t1["inc"]) if t1.get("cand") is not None else 0.0
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
        "exam_calls_per_task": exam_calls, "first_turn_gain": first_gain,
        "model_errors": end.get("model_errors", 0),
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
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results" / "runs"   # assay*.jsonl sits beside it
    found = sorted(d for d in root.iterdir() if (d / "log.jsonl").exists())
    loaded = [r for r in (load(d) for d in found) if r]
    # only replicates that finished in all five arms are analysed (PREREG.md)
    full = {rep for rep in {r["rep"] for r in loaded}
            if {r["arm"] for r in loaded if r["rep"] == rep} >= set(ARMS)}
    runs = [r for r in loaded if r["rep"] in full]
    left_out = sorted({d.name for d in found} - {r["run"] for r in runs})
    by_arm = {a: [r for r in runs if r["arm"] == a] for a in ARMS}
    seed_ref = None
    ref_path = HERE / "results" / "seed_exam.json"
    if ref_path.exists():
        seed_ref = json.loads(ref_path.read_text())
    lines = ["# Tables written by analyze.py from the run logs", "",
             f"Replicates complete in all five arms: {sorted(full)}. Runs left out: {', '.join(left_out) if left_out else 'none'}.", ""]

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
                        "twins_differ": sum(r["twins_differ"] for r in rs),
                        "exam_calls_per_task": statistics.mean(r["exam_calls_per_task"] for r in rs),
                        "final_bytes": statistics.mean(b for r in rs for b in r["final_bytes"].values() if b)
                        if any(b for r in rs for b in r["final_bytes"].values()) else None}
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
              "| Arm | " + " | ".join(f"t{t}" for t in range(1, 7)) + " |", "|---|" + "---|" * 6]
    for a in ARMS:
        cells = []
        for t in range(1, 7):
            pairs = [(ts[2], ts[3]) for r in by_arm[a] for ts in r["turn_scores"] if ts[0] == t and ts[2] is not None]
            cells.append("-" if not pairs else f"{statistics.mean(p[0] for p in pairs):.2f} to {statistics.mean(p[1] for p in pairs):.2f} (n={len(pairs)})")
        if by_arm[a]:
            lines.append(f"| {a} | " + " | ".join(cells) + " |")
    lines.append("")

    lines += ["## Size and economy", "", "| Arm | Pairs whose two final harnesses differ | Mean bytes of a final harness that was ever changed | Model calls used per exam task |",
              "|---|---|---|---|"]
    for a in ARMS:
        if a in arm_stats:
            st = arm_stats[a]
            lines.append(f"| {a} | {st['twins_differ']} of {st['n']} | {fmt(st['final_bytes'], 0)} | {fmt(st['exam_calls_per_task'], 2)} |")
    lines.append("")

    # ---- builder assay (M4) and first-turn gains
    assay = []
    for f in sorted((root.parent).glob("assay*.jsonl")):
        assay += [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    arm_of = {r["run"]: r["arm"] for r in runs}
    for ev in assay:
        ev["gain"] = (ev["cand"] - ev["inc"]) if ev.get("cand") is not None else 0.0
        ev["arm"] = arm_of.get(ev["run"])
    first = [r["first_turn_gain"] for r in runs]
    m4 = {}
    if assay:
        lines += ["## Builder assay", "", "Each run's final harness of slot A takes one build turn on a fresh seed harness. Gain is the candidate's mean minus the seed's mean on the same 9 fresh tasks, 0 when the candidate was discarded before the benchmark.", "",
                  "| Arm | Assays | Outcomes | Gains | Mean gain |", "|---|---|---|---|---|"]
        for a in ARMS:
            evs = [e for e in assay if e["arm"] == a]
            if evs:
                m4[a] = [e["gain"] for e in evs]
                lines.append(f"| {a} | {len(evs)} | {''.join(short[e['outcome']] for e in evs)} | "
                             f"{', '.join(f'{g:+.3f}' for g in m4[a])} | {statistics.mean(m4[a]):+.3f} |")
        lines += ["", f"First-turn gains of seed builders in this block (turn 1 of every run, same definition): "
                  f"{', '.join(f'{g:+.3f}' for g in first)}. Mean {statistics.mean(first):+.3f}.", ""]

    # ---- prediction verdicts
    def have(*arms):
        return all(x in arm_stats for x in arms)
    verdicts = []
    if seed_ref:
        sv, sh = statistics.mean(seed_ref["visible"]), statistics.mean(seed_ref["heldout"])
        per = {a: arm_stats[a]["visible_mean"] - sv for a in arm_stats}
        verdicts.append(("P1", all(v >= 0.10 for v in per.values()) if per else None,
                         "; ".join(f"{a} {v:+.3f}" for a, v in per.items()) + f" over the seed's {sv:.3f}"))
    for pid, x, y in (("P2", "twin-free-collective", "solo-pair"), ("P3", "twin-free-collective", "twin-fixed-builder")):
        if have(x, y):
            d = arm_stats[x]["visible_mean"] - arm_stats[y]["visible_mean"]
            verdicts.append((pid, abs(d) < 0.10, f"{x} minus {y} = {d:+.3f}"))
    if have("twin-stack-collective", "twin-free-collective"):
        d = arm_stats["twin-stack-collective"]["visible_mean"] - arm_stats["twin-free-collective"]["visible_mean"]
        verdicts.append(("P4", d > 0.03, f"stack minus free = {d:+.3f}"))
    if have("twin-free-rival", "twin-free-collective"):
        d1 = arm_stats["twin-free-rival"]["visible_mean"] - arm_stats["twin-free-collective"]["visible_mean"]
        d2 = arm_stats["twin-free-rival"]["heldout_mean"] - arm_stats["twin-free-collective"]["heldout_mean"]
        verdicts.append(("P5", abs(d1) < 0.10 and abs(d2) < 0.10, f"rival minus collective: visible {d1:+.3f}, held-out {d2:+.3f}"))
    all_out = [o for r in runs for o in r["outcomes"]]
    all_ed = [e for r in runs for e in r["edited"]]
    if all_out:
        verdicts.append(("P6", sum(all_ed) / len(all_ed) >= 0.75, f"{sum(all_ed)} of {len(all_ed)} build turns made an edit"))
        gate = [o for o in all_out if o in ("commit", "regress", "boot_fail")]
        disc = [o for o in gate if o != "commit"]
        verdicts.append(("P7", bool(gate) and len(disc) / len(gate) >= 0.10 and "boot_fail" in gate,
                         f"{len(disc)} of {len(gate)} candidates at the gate were discarded, {gate.count('boot_fail')} at boot"))
    if seed_ref and runs:
        g1 = statistics.mean(r["pair_visible"] for r in runs) - sv
        g2 = statistics.mean(r["pair_heldout"] for r in runs) - sh
        verdicts.append(("P8", g2 >= 0.5 * g1, f"pooled gain over the seed: visible {g1:+.3f}, held-out {g2:+.3f}"))
    live = [g for a in m4 if a != "twin-fixed-builder" for g in m4[a]]
    if live:
        d = statistics.mean(live) - statistics.mean(first)
        verdicts.append(("P9", abs(d) < 0.10, f"assay mean {statistics.mean(live):+.3f} over {len(live)} built harnesses, "
                         f"first-turn mean {statistics.mean(first):+.3f} over {len(first)} seed builders, difference {d:+.3f}"))
    lines += ["## Predictions", "", "| Prediction | Held | Figures |", "|---|---|---|"]
    for pid, ok, text in verdicts:
        lines.append(f"| {pid} | {'yes' if ok else 'no'} | {text} |")
    lines.append("")

    total = {"runs": len(runs), "usd": round(sum(r["usd"] for r in runs), 2), "calls": sum(r["calls"] for r in runs),
             "model_errors": sum(r["model_errors"] for r in runs)}
    lines += [f"Totals: {total['runs']} runs, {total['calls']} model calls, {total['usd']:.2f} dollars, "
              f"{total['model_errors']} model calls that failed on the referee's side.", ""]
    out = {"runs": runs, "arms": arm_stats, "contrasts": contrasts, "totals": total, "seed_exam": seed_ref,
           "assay": [{k: e.get(k) for k in ("run", "arm", "slot", "outcome", "inc", "cand", "gain")} for e in assay],
           "predictions": [{"id": p, "held": bool(ok), "figures": t} for p, ok, t in verdicts]}
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "summary.json").write_text(json.dumps(out, indent=1))
    (HERE / "results" / "tables.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
