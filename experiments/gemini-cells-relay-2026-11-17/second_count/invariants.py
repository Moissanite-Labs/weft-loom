#!/usr/bin/env python3
"""Log invariants over the 15 runs. Standard library only; reads logs and snapshots."""
import hashlib
import json
import os
from pathlib import Path

RUNS = Path("/srv/gc-live/runs")
REPS = ("-r0", "-r1", "-r2")
FAMS = ("ledger", "logwin", "bugfix")
HELD = ("stock", "spec")
MARGIN = 0.02


def rows_of(p):
    return [json.loads(x) for x in open(p) if x.strip()]


def instances(key, t, families, n):
    out = []
    for fam in families:
        for i in range(n):
            d = hashlib.sha256(f"{key}|{t}|{fam}|{i}".encode()).digest()
            out.append((fam, int.from_bytes(d[:4], "big") % 800000))
    return out


def tree_hash(root):
    h = hashlib.sha256()
    for p in sorted(q for q in Path(root).rglob("*") if q.is_file()):
        h.update(str(p.relative_to(root)).encode() + b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()[:16]


C = {}          # check name -> [checked, violations]
BAD = []


def chk(name, ok, where=""):
    c = C.setdefault(name, [0, 0])
    c[0] += 1
    if not ok:
        c[1] += 1
        BAD.append((name, where))


def main():
    names = sorted(d for d in os.listdir(RUNS) if d.endswith(REPS))
    exam_expected = [(f, 900000 + i) for f in FAMS for i in range(8)] + [(f, 900000 + i) for f in HELD for i in range(6)]
    all_bench_seeds = set()
    notes = []
    for name in names:
        rows = rows_of(RUNS / name / "log.jsonl")
        start = rows[0]
        end = [r for r in rows if r["kind"] == "end"][0]
        arm, spec, seed_h, secret = start["arm"], start["spec"], start["seed_harness"], end["secret"]
        chk("kinds are start,2 baseline,6 turn,2 exam,end", [r["kind"] for r in rows] ==
            ["start"] + ["baseline"] * 2 + ["turn"] * 6 + ["exam"] * 2 + ["end"], name)
        chk("sha256(revealed secret) == start.secret_sha256",
            hashlib.sha256(secret.encode()).hexdigest() == start["secret_sha256"], name)
        chk("config margin 0.02, 3 per family, level 3, 3 calls",
            (start["config"]["margin"], start["config"]["per_family"], start["config"]["level"],
             start["config"]["episode_calls"]) == (0.02, 3, 3, 3), name)
        H = {"A": seed_h, "B": seed_h}
        calls = usd = errs = 0
        for r in rows:
            if r["kind"] == "baseline":
                rep = r["report"]
                calls += rep["calls"]; usd += rep["usd"]; errs += rep["model_errors"]
                want = instances(f"{secret}|base|{r['slot']}", 0, FAMS, 3)
                got = [(e["family"], e["seed"]) for e in rep["episodes"]]
                chk("baseline seeds == hash(secret|base|slot)", got == want, name)
                chk("baseline harness == seed", r["harness"] == seed_h, name)
                all_bench_seeds.update(got)
                chk("benchmark report: zero model errors", rep["model_errors"] == 0, f"{name} baseline {r['slot']}")
            if r["kind"] != "turn":
                continue
            t = r["t"]
            w = f"{name} t{t}"
            me = "A" if t % 2 else "B"
            tgt = me if spec["topology"] == "solo" else ("B" if me == "A" else "A")
            chk("builder slot alternates A,B,A,..", r["builder"] == me, w)
            chk("target slot is as the arm says (solo: self, twin: other)", r["target"] == tgt, w)
            if arm == "twin-fixed-builder":
                chk("twin-fixed-builder: builder_harness == seed", r["builder_harness"] == seed_h, w)
            else:
                chk("other arms: builder_harness == builder's committed harness", r["builder_harness"] == H[me], w)
            if arm == "solo-pair":
                chk("solo-pair: builder == target", r["builder"] == r["target"], w)
            if arm == "twin-stack-collective":
                chk("stack: base == builder's committed harness", r["base"] == H[me], w)
            else:
                chk("non-stack: base == target's committed harness", r["base"] == H[tgt], w)
            chk("target_before == target's committed harness", r["target_before"] == H[tgt], w)
            chk("edited == (candidate != base)", r["edited"] == (r["candidate"] != r["base"]), w)
            chk("noop <=> candidate == target_before", (r["outcome"] == "noop") == (r["candidate"] == r["target_before"]), w)
            calls += r["build_calls"]; usd += r["build_usd"]; errs += r["build_model_errors"]
            chk("build turn: zero model errors", r["build_model_errors"] == 0, w)
            chk("build turn rc == 0", r["build_rc"] == 0, w)
            if r["outcome"] == "noop":
                chk("noop has no boot and no benchmark", "boot" not in r and "inc" not in r, w)
            else:
                chk("gated candidate has a boot row", "boot" in r, w)
                calls += r["boot"]["calls"]; errs += r["boot"]["model_errors"]
                notes.append(("boot_usd_missing", w))
            if r["outcome"] in ("commit", "regress"):
                ir, cr = r["inc_report"], r["cand_report"]
                calls += ir["calls"] + cr["calls"]; usd += ir["usd"] + cr["usd"]
                errs += ir["model_errors"] + cr["model_errors"]
                si = [(e["family"], e["seed"]) for e in ir["episodes"]]
                sc = [(e["family"], e["seed"]) for e in cr["episodes"]]
                chk("old and new harness ran the same 9 instances", si == sc and len(si) == 9, w)
                chk("turn seeds == hash(secret|candidate hash|t)", si == instances(f"{secret}|{r['candidate']}", t, FAMS, 3), w)
                all_bench_seeds.update(si)
                mi = sum(e["score"] for e in ir["episodes"]) / 9
                mc = sum(e["score"] for e in cr["episodes"]) / 9
                chk("inc/cand == mean of the 9 episode scores (to 4 dp)",
                    abs(mi - r["inc"]) < 6e-5 and abs(mc - r["cand"]) < 6e-5, w)
                chk("commit <=> cand >= inc - 0.02 (logged means)",
                    (r["outcome"] == "commit") == (r["cand"] >= r["inc"] - MARGIN), w)
                chk("commit <=> cand >= inc - 0.02 (means recomputed from episodes)",
                    (r["outcome"] == "commit") == (mc >= mi - MARGIN - 1e-9), w)
                chk("benchmark report: zero model errors", ir["model_errors"] == 0 and cr["model_errors"] == 0, w)
                if abs((r["cand"] - r["inc"]) + MARGIN) < 0.005:
                    notes.append(("gate within 0.005 of the threshold", f"{w} inc {r['inc']} cand {r['cand']} {r['outcome']}"))
            after = dict(H)
            if r["outcome"] == "commit":
                after[tgt] = r["candidate"]
            chk("harness_after: target replaced only on commit, builder slot untouched (twin)",
                r["harness_after"] == after, w)
            H = after
            ex = int(hashlib.sha256(f"{name}|ex|{t}".encode()).hexdigest()[:6], 16)
            chk("example-task seed is not an exam seed (900000..900007)", not (900000 <= ex <= 900007), w)
            notes.append(("example_seed", (name, t, ex)))
        chk("end.harness == state after turn 6", end["harness"] == H, name)
        exams = [r for r in rows if r["kind"] == "exam"]
        for e in exams:
            chk("exam row harness == final harness of its slot", e["harness"] == H[e["slot"]], name)
            got = [(x["family"], x["seed"]) for x in e["report"]["episodes"]]
            chk("exam instances are the fixed 36 (900000+i)", got == exam_expected, name)
            chk("exam report: zero model errors (log.jsonl)", e["report"]["model_errors"] == 0, f"{name} exam {e['slot']}")
        same = H["A"] == H["B"]
        chk("same final harness <=> identical exam report for A and B",
            same == (exams[0]["report"] == exams[1]["report"]), name)
        calls += exams[0]["report"]["calls"] + (0 if same else exams[1]["report"]["calls"])
        usd += exams[0]["report"]["usd"] + (0 if same else exams[1]["report"]["usd"])
        errs += exams[0]["report"]["model_errors"] + (0 if same else exams[1]["report"]["model_errors"])
        chk("end.calls == baseline + builds + boots + gate benchmarks + exam (shared exam once)", calls == end["calls"], f"{name} sum {calls} end {end['calls']}")
        chk("end.model_errors == sum of logged model errors", errs == end["model_errors"], f"{name} sum {errs} end {end['model_errors']}")
        notes.append(("usd_gap(end - logged parts, = boot cost not logged)", (name, round(end["usd"] - usd, 4))))
        for h in set(H.values()) | {seed_h}:
            p = RUNS / name / "snap" / h
            chk("snapshot of seed/final harness exists and re-hashes to its name", p.is_dir() and tree_hash(p) == h, f"{name} {h}")
        rp = RUNS / name / "exam_resit.jsonl"
        if rp.exists():
            rr = rows_of(rp)
            for e in rr:
                chk("resit: harness == final harness, fixed 36 instances, zero model errors",
                    e["harness"] == H[e["slot"]] and [(x["family"], x["seed"]) for x in e["report"]["episodes"]] == exam_expected
                    and e["report"]["model_errors"] == 0, name)
    chk("no gate/baseline seed is >= 800000 (exam seeds start at 900000)", max(s for _, s in all_bench_seeds) < 800000, "")
    exs = [v for k, v in notes if k == "example_seed"]
    hit = [(n, t, s) for n, t, s in exs for f in FAMS if (f, s) in all_bench_seeds]
    print("INVARIANT CHECKS (checked / violations)")
    for k, (n, bad) in C.items():
        print("%4d / %d  %s" % (n, bad, k))
    print()
    print("VIOLATIONS")
    for b in BAD:
        print("  ", b)
    if not BAD:
        print("   none")
    print()
    print("NOTES")
    print("example-task seeds: %d turns, range %d..%d, equal to a gate/baseline seed of any run: %d, in exam range: %d"
          % (len(exs), min(s for _, _, s in exs), max(s for _, _, s in exs), len(hit),
             sum(1 for _, _, s in exs if 900000 <= s <= 900007)))
    for k, v in notes:
        if k.startswith("gate within") or k.startswith("usd_gap"):
            print("  ", k, v)
    print("distinct (family, seed) gate/baseline instances over 15 runs:", len(all_bench_seeds))


if __name__ == "__main__":
    main()
