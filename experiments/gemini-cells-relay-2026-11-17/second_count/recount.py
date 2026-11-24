#!/usr/bin/env python3
"""Independent second count of the gemini-cells relay record.

Standard library only. Derived from PREREG.md's wording and the log rows; analyze.py and
explore.py were not opened. Reads /srv/gc-live/runs/<arm>-r{0,1,2}/log.jsonl.
"""
import itertools
import json
import os
from fractions import Fraction

RUNS = "/srv/gc-live/runs"
SEED_EXAM = ("/home/user/weft-loom/experiments/gemini-cells-relay-2026-11-17/"
             "results/seed_exam.json")
REPS = ("-r0", "-r1", "-r2")
VISIBLE = ("ledger", "logwin", "bugfix")
HELDOUT = ("stock", "spec")
ARMS = ("twin-free-rival", "twin-free-collective", "twin-stack-collective",
        "solo-pair", "twin-fixed-builder")
OUTCOMES = ("commit", "regress", "boot_fail", "invalid", "noop")
RESIT = {"twin-stack-collective-r2": "exam_resit.jsonl"}


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def rows_of(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def slot_mean(report, fams):
    """Mean over the exam episodes whose family is in fams (episode-level mean)."""
    sc = [e["score"] for e in report["episodes"] if e["family"] in fams]
    return mean(sc), len(sc)


def load_run(name):
    rows = rows_of(os.path.join(RUNS, name, "log.jsonl"))
    start = [r for r in rows if r["kind"] == "start"][0]
    end = [r for r in rows if r["kind"] == "end"]
    assert len(end) == 1, name + ": no single end row"
    end = end[0]
    turns = sorted((r for r in rows if r["kind"] == "turn"), key=lambda r: r["t"])
    exams = [r for r in rows if r["kind"] == "exam"]
    src = "log.jsonl"
    if name in RESIT:
        exams = [r for r in rows_of(os.path.join(RUNS, name, RESIT[name])) if r["kind"] == "exam"]
        src = RESIT[name]
    by_slot = {r["slot"]: r for r in exams}
    assert set(by_slot) == {"A", "B"} and len(exams) == 2, name + ": exam rows"
    m1s, m2s, nv, nh, exam_errs = [], [], [], [], 0
    for s in ("A", "B"):
        assert by_slot[s]["harness"] == end["harness"][s], name + ": exam harness != end harness"
        v, n1 = slot_mean(by_slot[s]["report"], VISIBLE)
        h, n2 = slot_mean(by_slot[s]["report"], HELDOUT)
        m1s.append(v), m2s.append(h), nv.append(n1), nh.append(n2)
    same = end["harness"]["A"] == end["harness"]["B"]
    exam_errs = by_slot["A"]["report"]["model_errors"] + (0 if same else by_slot["B"]["report"]["model_errors"])
    return {"name": name, "arm": start["arm"], "rep": start["rep"], "start": start, "end": end,
            "turns": turns, "M1": mean(m1s), "M2": mean(m2s), "M1_slots": m1s, "M2_slots": m2s,
            "n_vis": nv, "n_held": nh, "differ": not same, "exam_src": src,
            "exam_model_errors": exam_errs,
            "exam_calls": by_slot["A"]["report"]["calls"] + (0 if same else by_slot["B"]["report"]["calls"]),
            "exam_usd": by_slot["A"]["report"]["usd"] + (0 if same else by_slot["B"]["report"]["usd"])}


def perm_p(xs, ys):
    """Exact two-sided permutation p for a difference of means: every way of dealing the
    pooled runs into groups of the observed sizes, p = share with |diff| >= |observed|
    (observed labelling included; ties count, with a 1e-12 tolerance)."""
    pool = list(xs) + list(ys)
    n, k = len(pool), len(xs)
    obs = mean(xs) - mean(ys)
    hit = tot = 0
    for idx in itertools.combinations(range(n), k):
        a = [pool[i] for i in idx]
        b = [pool[i] for i in range(n) if i not in idx]
        d = mean(a) - mean(b)
        tot += 1
        if abs(d) >= abs(obs) - 1e-12:
            hit += 1
    return obs, Fraction(hit, tot), hit, tot


def verdict(ok):
    return "PASS" if ok else "FAIL"


def main():
    names = sorted(d for d in os.listdir(RUNS) if d.endswith(REPS))
    runs = [load_run(n) for n in names]
    assert len(runs) == 15, len(runs)
    seed = json.load(open(SEED_EXAM))
    seed_v, seed_h = mean(seed["visible"]), mean(seed["heldout"])
    assert len(seed["visible"]) == 12 and len(seed["heldout"]) == 12

    print("SECOND COUNT, 15 runs (names ending -r0, -r1, -r2)")
    print("seed exam level (mean of 12 sittings): visible %.4f  held-out %.4f" % (seed_v, seed_h))
    print()
    print("PER RUN")
    print("%-26s %7s %7s  %-13s %-13s %s  %s" % ("run", "M1", "M2", "M1 A/B", "M2 A/B", "final differ", "exam source"))
    for r in runs:
        print("%-26s %7.4f %7.4f  %.3f/%.3f   %.3f/%.3f   %-5s         %s" % (
            r["name"], r["M1"], r["M2"], r["M1_slots"][0], r["M1_slots"][1],
            r["M2_slots"][0], r["M2_slots"][1], r["differ"], r["exam_src"]))
        assert r["n_vis"] == [24, 24] and r["n_held"] == [12, 12], (r["name"], r["n_vis"], r["n_held"])
    print()
    print("PER RUN TURNS  (t:builder>target outcome, e=builder edited, -=no edit)")
    for r in runs:
        cells = ["%d:%s>%s %s%s" % (t["t"], t["builder"], t["target"], t["outcome"],
                                    " e" if t["edited"] else " -") for t in r["turns"]]
        print("%-26s %s" % (r["name"], " | ".join(cells)))
        assert len(r["turns"]) == 6, r["name"]
    print()

    print("PER ARM")
    print("%-22s %2s %7s %7s  %s  %s  %s" % ("arm", "n", "M1", "M2", " ".join("%9s" % o for o in OUTCOMES),
                                         "edited", "pairs differ"))
    arm_m1, arm_m2 = {}, {}
    tot_out = dict.fromkeys(OUTCOMES, 0)
    tot_edit = tot_turns = 0
    for arm in ARMS:
        rs = [r for r in runs if r["arm"] == arm]
        arm_m1[arm] = [r["M1"] for r in rs]
        arm_m2[arm] = [r["M2"] for r in rs]
        cnt = dict.fromkeys(OUTCOMES, 0)
        ed = nt = 0
        for r in rs:
            for t in r["turns"]:
                cnt[t["outcome"]] += 1
                tot_out[t["outcome"]] += 1
                ed += bool(t["edited"])
                nt += 1
        tot_edit += ed
        tot_turns += nt
        print("%-22s %2d %7.4f %7.4f  %s  %2d/%2d   %d/%d" % (
            arm, len(rs), mean(arm_m1[arm]), mean(arm_m2[arm]),
            " ".join("%9d" % cnt[o] for o in OUTCOMES), ed, nt,
            sum(r["differ"] for r in rs), len(rs)))
    print("%-22s %2d %7.4f %7.4f  %s  %2d/%2d   %d/%d" % (
        "ALL", len(runs), mean(r["M1"] for r in runs), mean(r["M2"] for r in runs),
        " ".join("%9d" % tot_out[o] for o in OUTCOMES), tot_edit, tot_turns,
        sum(r["differ"] for r in runs), len(runs)))
    print()

    print("CONTRASTS (difference of arm means, exact two-sided permutation p over run labels)")
    contrasts = [("twin-free-collective", "solo-pair"),
                 ("twin-free-collective", "twin-fixed-builder"),
                 ("twin-stack-collective", "twin-free-collective"),
                 ("twin-free-rival", "twin-free-collective")]
    D = {}
    for a, b in contrasts:
        for label, table in (("M1", arm_m1), ("M2", arm_m2)):
            d, p, hit, tot = perm_p(table[a], table[b])
            D[(a, b, label)] = d
            print("%-22s minus %-22s %s  diff %+.4f  p = %d/%d = %.3f" % (a, b, label, d, hit, tot, float(p)))
    print("(3 runs per arm: 20 relabellings, smallest possible two-sided p is 2/20 = 0.100)")
    print()

    print("PREDICTIONS")
    am1 = {a: mean(v) for a, v in arm_m1.items()}
    p1_each = {a: am1[a] - seed_v for a in ARMS}
    print("P1 %s: every arm's mean M1 >= seed visible + 0.10 = %.4f.  margins over seed: %s" % (
        verdict(all(v >= 0.10 for v in p1_each.values())), seed_v + 0.10,
        ", ".join("%s %+.4f" % (a, v) for a, v in p1_each.items())))
    d = D[("twin-free-collective", "solo-pair", "M1")]
    print("P2 %s: |twin-free-collective - solo-pair| on M1 = %.4f, pass mark <= 0.10" % (verdict(abs(d) <= 0.10), abs(d)))
    d = D[("twin-free-collective", "twin-fixed-builder", "M1")]
    print("P3 %s: |twin-free-collective - twin-fixed-builder| on M1 = %.4f, pass mark <= 0.10" % (verdict(abs(d) <= 0.10), abs(d)))
    d = D[("twin-stack-collective", "twin-free-collective", "M1")]
    print("P4 %s: twin-stack-collective - twin-free-collective on M1 = %+.4f, pass mark > 0.03" % (verdict(d > 0.03), d))
    d1 = D[("twin-free-rival", "twin-free-collective", "M1")]
    d2 = D[("twin-free-rival", "twin-free-collective", "M2")]
    print("P5 %s: |rival - collective| M1 = %.4f, M2 = %.4f, pass mark both <= 0.10" % (
        verdict(abs(d1) <= 0.10 and abs(d2) <= 0.10), abs(d1), abs(d2)))
    print("P6 %s: builder edited in %d of %d build turns = %.1f%%, pass mark >= 75%%" % (
        verdict(tot_edit / tot_turns >= 0.75), tot_edit, tot_turns, 100.0 * tot_edit / tot_turns))
    reach = tot_turns - tot_out["noop"]
    disc = tot_out["regress"] + tot_out["boot_fail"] + tot_out["invalid"]
    p7 = disc / reach >= 0.10 and tot_out["boot_fail"] >= 1
    print("P7 %s: %d of %d candidates that reached the gate were discarded = %.1f%% (pass mark >= 10%%); "
          "discarded at boot: %d (pass mark >= 1)" % (verdict(p7), disc, reach, 100.0 * disc / reach, tot_out["boot_fail"]))
    reach_b = reach - tot_out["invalid"]
    disc_b = tot_out["regress"] + tot_out["boot_fail"]
    print("   variant (surface-rule discards left out of both counts): %d of %d = %.1f%%" % (
        disc_b, reach_b, 100.0 * disc_b / reach_b if reach_b else float("nan")))
    edited_reach = sum(1 for r in runs for t in r["turns"] if t["outcome"] != "noop" and t["edited"])
    edited_disc = sum(1 for r in runs for t in r["turns"] if t["outcome"] in ("regress", "boot_fail", "invalid") and t["edited"])
    print("   variant (only gated candidates the builder edited): %d of %d = %.1f%%" % (
        edited_disc, edited_reach, 100.0 * edited_disc / edited_reach))
    g1 = mean(r["M1"] for r in runs) - seed_v
    g2 = mean(r["M2"] for r in runs) - seed_h
    print("P8 %s: pooled gain M1 %+.4f, M2 %+.4f, ratio %.3f, pass mark M2 gain >= half of M1 gain (%.4f)" % (
        verdict(g2 >= 0.5 * g1), g1, g2, g2 / g1 if g1 else float("nan"), 0.5 * g1))
    print("P9 skipped: needs builder assay rows, which do not exist yet")
    print()

    print("TOTALS over the 15 end rows")
    calls = sum(r["end"]["calls"] for r in runs)
    usd = sum(r["end"]["usd"] for r in runs)
    errs = sum(r["end"]["model_errors"] for r in runs)
    print("model calls %d   dollars %.4f   model_errors %d" % (calls, usd, errs))
    for r in runs:
        if r["end"]["model_errors"]:
            print("  %s: end row model_errors %d" % (r["name"], r["end"]["model_errors"]))
    for name in RESIT:
        r = [x for x in runs if x["name"] == name][0]
        print("  not in any end row: resit exam of %s, %d calls, %.4f dollars, %d model errors"
              % (name, r["exam_calls"], r["exam_usd"], r["exam_model_errors"]))
    print("  per run: " + "; ".join("%s %d calls $%.2f" % (r["name"], r["end"]["calls"], r["end"]["usd"]) for r in runs))
    print()

    print("DEFINITIONS USED")
    print("- M1/M2 slot value: plain mean over that slot's exam episodes of the family set (24 visible, 12 held-out);")
    print("  equal to the mean of family means because families have equal counts. Run value = mean of slots A and B.")
    print("- When the two final harnesses are identical the log carries the same report for both slots; both rows are used as logged.")
    print("- twin-stack-collective-r2: exam taken from exam_resit.jsonl, not log.jsonl.")
    print("- Seed level: mean of the 12 values in seed_exam.json 'visible' (for M1) and 'heldout' (for M2).")
    print("- 'within 0.10': absolute difference of arm means <= 0.10 (boundary counts as within).")
    print("- 'edit': the log's `edited` flag (candidate tree hash != the hash the candidate started from).")
    print("- P7 denominator: every turn whose outcome is not noop (invalid, boot_fail, regress, commit);")
    print("  discarded = invalid + boot_fail + regress. Two variants printed.")
    print("- P8: (mean M2 over 15 runs - seed held-out) >= 0.5 * (mean M1 over 15 runs - seed visible).")
    print("- Permutation p: all C(6,3)=20 relabellings, share with |diff| >= |observed|, ties included.")
    print("- Totals: end-row calls, usd, model_errors as logged; the resit's cost is shown apart.")


if __name__ == "__main__":
    main()
