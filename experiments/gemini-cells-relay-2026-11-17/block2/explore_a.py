#!/usr/bin/env python3
"""Exploratory reading of part A, written after its planned analysis was seen. Nothing
here was preregistered, and nothing here can change the verdicts of block2/analyze_a.py.

    python3 -I -B block2/explore_a.py block2/partA/assay2-partA-*.jsonl > block2/explore_a.out

1. Retest: each run's single pilot assay (slot A) beside the mean of part A's three assays
   of the same slot-A harness, with Pearson and Spearman correlations over the 19 runs and
   an exact-enough permutation p (20,000 shuffles, fixed seed).
2. Where the pilot's gap went: arm means on slot A only (the slot the pilot assayed), from
   the pilot's single assays and from part A's three.
3. How much one assay says about a harness: variance of gains between harnesses and between
   assays of one harness (one-way random effects over distinct harnesses, by hash), the
   intraclass correlation, and by the Spearman-Brown formula the reliability of a mean of
   1, 3, 6 and 12 assays.
4. Whether no-edit is a trait of a harness or a coin each time: the number of no-edit
   assays per distinct harness against a binomial with the pooled rate, and the step limit
   and calls per build of the harnesses that did not edit.
5. The spread of run values by arm, the number part B's power depends on.
"""

import glob
import json
import math
import pathlib
import random
import statistics
import sys
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analyze_a import ARMS, FREE, RUNS, SEEDB, SOLO, arm_of, exact_p, fault, gain  # noqa: E402

ROOT = HERE.parent


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(x, y):
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else float("nan")


def perm_p(x, y, stat, n=20000, seed=20261124):
    rng = random.Random(seed)
    obs = abs(stat(x, y))
    y = list(y)
    hits = 0
    for _ in range(n):
        rng.shuffle(y)
        hits += abs(stat(x, y)) >= obs - 1e-12
    return (hits + 1) / (n + 1)


def main(argv):
    rows = [json.loads(line) for pattern in argv for path in sorted(glob.glob(pattern)) for line in open(path)]
    rows = [r for r in rows if r.get("kind") == "assay2" and not fault(r)]
    pilot = [json.loads(line) for path in sorted(glob.glob(str(ROOT / "results" / "assay-*of4.jsonl")))
             for line in open(path)]
    pilot = {r["run"]: r for r in pilot if r.get("kind") == "assay" and r["run"] in RUNS}
    out = ["Exploratory, written after the planned analysis was seen. Not preregistered.", ""]

    # 1. Retest
    new_a = defaultdict(list)
    for r in rows:
        if r["run"] in RUNS and r["slot"] == "A":
            new_a[r["run"]].append(gain(r))
    runs = sorted(set(pilot) & set(new_a))
    x = [gain(pilot[k]) for k in runs]
    y = [statistics.fmean(new_a[k]) for k in runs]
    first = [new_a[k][0] for k in runs]
    out += ["## 1. Retest of the pilot's single assays (slot A, same harness)", "",
            "| Run | Pilot assay | Part A, three assays | Part A mean |", "|---|---|---|---|"]
    for k, a, b in zip(runs, x, y):
        out.append(f"| {k} | {a:+.3f}{' (no edit)' if pilot[k].get('outcome') == 'noop' else ''} | "
                   + ", ".join(f"{g:+.3f}" for g in new_a[k]) + f" | {b:+.3f} |")
    rp, rs = pearson(x, y), pearson(ranks(x), ranks(y))
    out += ["", f"Over {len(runs)} runs, pilot assay against part A's mean of three: Pearson {rp:+.3f}"
                f" (permutation p {perm_p(x, y, pearson):.3f}), Spearman {rs:+.3f}"
                f" (permutation p {perm_p(ranks(x), ranks(y), pearson):.3f}).",
            f"Pilot assay against part A's first assay alone (one against one): Pearson {pearson(x, first):+.3f}.",
            ""]

    # 2. Slot A arm means, pilot against part A
    new_b = defaultdict(list)
    for r in rows:
        if r["run"] in RUNS and r["slot"] == "B":
            new_b[r["run"]].append(gain(r))
    out += ["## 2. Arm means by slot", "",
            "| Arm | Slot A, pilot, one assay a run | Slot A, part A, three a run | Slot B, part A, three a run |",
            "|---|---|---|---|"]
    for arm in ARMS:
        ks = [k for k in runs if arm_of(k) == arm]
        if ks:
            out.append(f"| {arm} | {statistics.fmean(gain(pilot[k]) for k in ks):+.3f} |"
                       f" {statistics.fmean(statistics.fmean(new_a[k]) for k in ks):+.3f} |"
                       f" {statistics.fmean(statistics.fmean(new_b[k]) for k in ks):+.3f} |")
    fa = [statistics.fmean(new_a[k]) for k in runs if arm_of(k) == FREE]
    sa = [statistics.fmean(new_a[k]) for k in runs if arm_of(k) == SOLO]
    ba = [statistics.fmean(new_a[k]) for k in runs if arm_of(k) == SEEDB]
    out += ["", f"The planned contrasts on slot A alone, part A's assays: free minus solo"
                f" {statistics.fmean(fa) - statistics.fmean(sa):+.3f} (exact p {exact_p(fa, sa):.4f}),"
                f" free minus seed builder {statistics.fmean(fa) - statistics.fmean(ba):+.3f}"
                f" (exact p {exact_p(fa, ba):.4f}). Chosen after seeing the data, so not a test of anything.", ""]

    # 3. Variance components over distinct harnesses
    by_h = defaultdict(list)
    for r in rows:
        by_h[r["builder_harness"]].append(gain(r))
    groups = list(by_h.values())
    sizes = Counter(len(g) for g in groups)
    n_tot = sum(len(g) for g in groups)
    grand = statistics.fmean(v for g in groups for v in g)
    ssb = sum(len(g) * (statistics.fmean(g) - grand) ** 2 for g in groups)
    ssw = sum((v - statistics.fmean(g)) ** 2 for g in groups for v in g)
    a = len(groups)
    msb, msw = ssb / (a - 1), ssw / (n_tot - a)
    n0 = (n_tot - sum(len(g) ** 2 for g in groups) / n_tot) / (a - 1)
    var_b = max(0.0, (msb - msw) / n0)
    icc = var_b / (var_b + msw)
    out += ["## 3. How much one assay says about a harness", "",
            f"{a} distinct harnesses (assays each: " + ", ".join(f"{n}: {c}" for n, c in sorted(sizes.items()))
            + f"), {n_tot} assays. Between-harness variance {var_b:.4f} (SD {math.sqrt(var_b):.3f}),"
              f" between-assay variance within a harness {msw:.4f} (SD {math.sqrt(msw):.3f}).",
            f"Intraclass correlation {icc:.3f}. Reliability of a harness's mean gain over k assays"
            f" (Spearman-Brown): " + ", ".join(f"k={k}: {k * icc / (1 + (k - 1) * icc):.2f}" for k in (1, 3, 6, 12))
            + ".", ""]

    # 4. No-edit as a trait
    built = defaultdict_rows(rows)
    noops = [sum(1 for r in rs_ if r.get("outcome") == "noop") for rs_ in built.values()]
    counts = [len(rs_) for rs_ in built.values()]
    rate = sum(noops) / sum(counts)
    three = [(n, c) for n, c in zip(noops, counts) if c == 3]
    obs = Counter(n for n, _ in three)
    exp = {k: len(three) * math.comb(3, k) * rate ** k * (1 - rate) ** (3 - k) for k in range(4)}
    out += ["## 4. No edit: a trait of the harness or chance each time", "",
            f"Pooled no-edit rate over built harnesses {rate:.3f}. Harnesses with three assays: {len(three)}.",
            "", "| No-edit assays of 3 | Harnesses | Expected if every harness had the pooled rate |",
            "|---|---|---|"]
    for k in range(4):
        out.append(f"| {k} | {obs.get(k, 0)} | {exp[k]:.1f} |")
    out += ["", "Harnesses with any no-edit assay:", ""]
    for h, rs_ in sorted(built.items(), key=lambda kv: (kv[1][0]["run"], kv[1][0]["slot"])):
        n = sum(1 for r in rs_ if r.get("outcome") == "noop")
        if n:
            names = sorted({f"{r['run']} {r['slot']}" for r in rs_})
            out.append(f"- {' = '.join(names)}: {n} of {len(rs_)}")
    by_arm = Counter()
    for rs_ in built.values():
        if all(r.get("outcome") == "noop" for r in rs_):
            by_arm[arm_of(rs_[0]["run"])] += 1
    out += ["", "Harnesses that never edited, by arm: "
            + ", ".join(f"{arm} {by_arm.get(arm, 0)}" for arm in ARMS) + ".", ""]
    out += ["Step limit (`MAX_STEPS` in the harness's agent.py, read from the record's archive) and the"
            " model calls of each build, for every harness with a no-edit assay or a limit other than the"
            " seed's 40. A build turn allows 16 calls.", "",
            "| Harness | MAX_STEPS | No-edit assays | Calls per build |", "|---|---|---|---|"]
    for h, rs_ in sorted(built.items(), key=lambda kv: (kv[1][0]["run"], kv[1][0]["slot"])):
        cap = max_steps(rs_[0]["run"], h)
        n = sum(1 for r in rs_ if r.get("outcome") == "noop")
        if n or cap != 40:
            names = " = ".join(sorted({f"{r['run']} {r['slot']}" for r in rs_}))
            out.append(f"| {names} | {cap if cap is not None else 'none'} | {n} of {len(rs_)} |"
                       f" {', '.join(str(r.get('build_calls')) for r in rs_)} |")
    out.append("")

    # 5. Spread of run values by arm
    per_run = defaultdict(list)
    for r in rows:
        if r["run"] in RUNS:
            per_run[r["run"]].append(gain(r))
    out += ["## 5. Spread of run values (mean of six assays) by arm", "", "| Arm | Runs | SD of run values |",
            "|---|---|---|"]
    for arm in ARMS:
        v = [statistics.fmean(g) for k, g in per_run.items() if arm_of(k) == arm]
        if len(v) > 1:
            out.append(f"| {arm} | {len(v)} | {statistics.stdev(v):.3f} |")
    pooled = [statistics.fmean(g) for k, g in per_run.items() if arm_of(k) in (FREE, SOLO, SEEDB)]
    out += ["", f"Pooled over free, solo and seed-builder runs, ignoring arm: SD {statistics.stdev(pooled):.3f}"
                f" over {len(pooled)} runs."]
    print("\n".join(out))
    return 0


def max_steps(run, harness):
    """MAX_STEPS = n in the harness's agent.py, from the run's packed archive."""
    import re
    import tarfile
    with tarfile.open(ROOT / "results" / "runs" / run / "artifacts.tar.gz") as tf:
        try:
            text = tf.extractfile(f"snap/{harness}/agent.py").read().decode("utf-8", "replace")
        except KeyError:
            return None
    m = re.search(r"^MAX_STEPS\s*=\s*(\d+)", text, re.M)
    return int(m.group(1)) if m else None


def defaultdict_rows(rows):
    d = defaultdict(list)
    for r in rows:
        if r["run"] in RUNS:
            d[r["builder_harness"]].append(r)
    return d


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
