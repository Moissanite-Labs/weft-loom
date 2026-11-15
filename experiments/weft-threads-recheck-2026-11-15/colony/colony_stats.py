#!/usr/bin/env python3
"""colony_stats.py: offline re-analysis of the razi-cells "colony laws" record from committed raw data.

Reads (never writes) the weft-loom checkout. Writes only colony_results.json next to this script.
No network, no model calls.

  /path/to/python colony_stats.py [--quick]

Every number printed is recomputed from raw files. Each block prints `SRC file :: field` lines.
Run-level statistics use the RUN as the unit of replication (cells inside a run share a library, pool energy
through rest-gifts, and share the provider prompt cache, so they are not independent).
"""
import hashlib
import itertools
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import stats

# repository root = three levels above this file (<root>/experiments/<record>/colony/colony_stats.py)
LOOM = Path(os.environ.get("LOOM", str(Path(__file__).resolve().parents[3])))
ARCH = LOOM / "archive/razi-cells-exp-2026-11"
LAWS = LOOM / "experiments/razi-cells-laws-2026-11"
BLITZ = LOOM / "experiments/openai-cells-blitz-2026-11-12"
NL = LOOM / "experiments/no-language-colony-2026-11-12"
def _weft_arg():
    a = sys.argv
    if "--weft" in a and a.index("--weft") + 1 < len(a):
        return Path(a[a.index("--weft") + 1])
    if os.environ.get("WEFT_CHECKOUT"):
        return Path(os.environ["WEFT_CHECKOUT"])
    return None


WEFT = _weft_arg()  # the weft software checkout; only PART 3b (git history) needs it
HERE = Path(__file__).resolve().parent
KITS = ("compress", "fibmod", "csvsum", "maze")
BOOT = 20000
SEED = 20261115
OUT = {}
USED = {}  # path -> sha256, filled by readers


def fail(msg):
    raise SystemExit("colony_stats FAILED: " + msg)


def src(path, field):
    print(f"    SRC {Path(path).relative_to(LOOM) if str(path).startswith(str(LOOM)) else path} :: {field}")


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def read_text(p):
    p = Path(p)
    if not p.exists():
        fail(f"missing file {p}")
    USED[str(p)] = _sha(p)
    return p.read_text()


def jl(p):
    return [json.loads(l) for l in read_text(p).splitlines() if l.strip()]


def jf(p):
    return json.loads(read_text(p))


# ---------------------------------------------------------------- statistics helpers
def cp(k, n, alpha=0.05):
    lo = 0.0 if k == 0 else stats.beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(1 - alpha / 2, k + 1, n - k)
    return lo, hi


def perm_exact(a, b, stat=lambda x, y: np.mean(x) - np.mean(y)):
    """Exact two-sided permutation test over all splits of the pooled runs. Returns (obs, p, n_splits)."""
    a, b = list(a), list(b)
    pool = np.array(a + b, float)
    n = len(a)
    obs = stat(np.array(a, float), np.array(b, float))
    cnt = tot = 0
    idx = range(len(pool))
    for comb in itertools.combinations(idx, n):
        m = np.zeros(len(pool), bool)
        m[list(comb)] = True
        s = stat(pool[m], pool[~m])
        tot += 1
        if abs(s) >= abs(obs) - 1e-12:
            cnt += 1
    return obs, cnt / tot, tot


def boot_ci(a, b, fn, B=BOOT, seed=SEED, alpha=0.05):
    """Percentile bootstrap over RUNS (resample runs within each arm). fn(a_sample, b_sample) -> scalar."""
    rng = np.random.default_rng(seed)
    a, b = np.array(a, float), np.array(b, float)
    vals = np.empty(B)
    for i in range(B):
        vals[i] = fn(rng.choice(a, len(a)), rng.choice(b, len(b)))
    vals = vals[np.isfinite(vals)]
    return float(np.percentile(vals, 100 * alpha / 2)), float(np.percentile(vals, 100 * (1 - alpha / 2)))


def holm(pvals):
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    adj, run = {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        adj[k] = run
    return adj


def fmt(x, d=4):
    return f"{x:.{d}f}"


# ---------------------------------------------------------------- integrity of the raw files used
def sums_table():
    t = {}
    for l in read_text(ARCH / "SHA256SUMS.txt").splitlines():
        h, _, rel = l.partition("  ")
        t[rel] = h
    return t


def manifest_table():
    t = {}
    for l in read_text(LAWS / "manifest.md").splitlines():
        m = re.match(r"\|\s*(\S+)\s*\|\s*([0-9a-f]{64})\s*\|", l)
        if m:
            t[m.group(1)] = m.group(2)
    return t


def check_integrity():
    S, M = sums_table(), manifest_table()
    bad, ok, unk = [], 0, []
    for p, h in USED.items():
        pp = Path(p)
        if str(pp).startswith(str(ARCH)):
            rel = str(pp.relative_to(ARCH))
            ref = S.get(rel)
        elif str(pp).startswith(str(LAWS)):
            rel = str(pp.relative_to(LAWS))
            ref = M.get(rel)
        else:
            ref, rel = None, str(pp)
        if ref is None:
            unk.append(rel)
        elif ref != h:
            bad.append(rel)
        else:
            ok += 1
    print(f"\n[integrity] files read {len(USED)}; sha256 match archive SHA256SUMS.txt / laws manifest.md: {ok}; "
          f"no recorded hash: {len(unk)}; MISMATCH: {len(bad)}")
    if unk:
        print("    no recorded hash (outside both tables):", sorted(unk)[:8], "..." if len(unk) > 8 else "")
    hard = [b for b in bad if not b.endswith(".md")]
    if bad:
        print("    MISMATCH files:", bad, "(prose files compared with manifest.md; see the TESTS.md blob comparison in part 3b)")
    if hard:
        fail("sha256 mismatch in data files: " + ", ".join(hard[:10]))
    OUT["integrity"] = {"read": len(USED), "match": ok, "no_hash": len(unk), "mismatch": len(bad)}


# ---------------------------------------------------------------- SP3 data
def load_cell(run, kit, led):
    R = jl(ARCH / run / kit / "log.jsonl")
    laws = next((r for r in R if r.get("event") == "laws"), {})
    use = [r for r in R if isinstance(r.get("usage"), dict)]
    models = [r["model"] for r in use]
    acts = [r for r in R if "act" in r and "step" in r]
    born = (laws.get("start") or [models[0] if models else None])[0]
    fn = next((r["next"] for r in acts if r.get("next")), None)  # B1 definition of sp3.py
    evs = [r.get("event") for r in R if "event" in r]
    seen, pre, post = False, 0.0, 0.0
    for r in R:
        if r.get("event") == "assay":
            seen = True
        if isinstance(r.get("usage"), dict):
            if seen:
                post += r["cost"]
            else:
                pre += r["cost"]
    L = led[kit]
    rest = next((r for r in R if r.get("event") == "rest"), None)
    return {
        "run": run, "kit": kit, "laws": laws, "born": born, "models": models, "first_next": fn[0] if fn else None,
        "light0": bool(fn) and fn[0] == "light" and born != "light",
        "death": evs.count("death"), "apop": evs.count("apoptosis"), "downshift": evs.count("downshift"),
        "overdraft": evs.count("overdraft"), "assayed": "assay" in evs,
        "state": L["state"], "spent": L["spent"], "got": L["got"], "gave": L["gave"], "e": L["e"],
        "left": L["gave"] + L["e"], "pre": pre, "post": post, "rested": rest is not None,
        "steps": len(models),
        "rounds_after": 0,
    }


def load_run(run):
    led = jf(ARCH / run / ".ledger.json")
    return [load_cell(run, k, led) for k in KITS]


SP3 = {a: [f"s3{a}{i}" for i in "1234"] for a in "abcd"}
WANT = {"a": (True, False), "b": (False, False), "c": (True, True), "d": (False, True)}


def sp3_cells():
    cells = {}
    for a, runs in SP3.items():
        cells[a] = {r: load_run(r) for r in runs}
        for r, cs in cells[a].items():
            for c in cs:
                got = (c["laws"].get("price_show"), c["laws"].get("sense_show"))
                if got != WANT[a]:
                    fail(f"{r}/{c['kit']} laws row {got} does not match arm {a} {WANT[a]}")
                if c["born"] != "mid":
                    fail(f"{r}/{c['kit']} not born on mid")
    return cells


def rel_table(path):
    rows = jf(path)
    return {(r["run"], r["kit"]): (r["rel"] or 0.0) for r in rows if r["run"] != "ref"}


def o1(rel, run, kits=KITS):
    return statistics.median([rel.get((run, k), 0.0) for k in kits])


def run_spent(cs):
    return sum(c["spent"] for c in cs)


# ================================================================ claim (a)
def claim_a(sp3):
    print("\n" + "=" * 100 + "\nCLAIM (a): price display moves cells to the cheapest model (14 of 16 at the first step)")
    src(ARCH / "s3a1/<kit>/log.jsonl", "first act event carrying `next` -> next[0]; events `laws` (price_show, sense_show, start)")
    res = {}
    cnt = {a: sum(c["light0"] for r in sp3[a].values() for c in r) for a in "abcd"}
    print("  cells choosing light at step 0 (born on mid), SP3, by arm:", {a: f"{cnt[a]}/16" for a in cnt})
    choice = {a: {} for a in "abcd"}
    for a in "abcd":
        for r in sp3[a].values():
            for c in r:
                choice[a][c["first_next"]] = choice[a].get(c["first_next"], 0) + 1
    print("  model chosen after step 0 (first `next`), by arm:", choice)
    for a in "abcd":
        per_run = [sum(c["light0"] for c in sp3[a][r]) for r in SP3[a]]
        print(f"    arm {a} per-run counts (of 4 cells each): {per_run}")
    k, n = cnt["a"], 16
    lo, hi = cp(k, n)
    bt = stats.binomtest(k, n, 1 / 3, alternative="two-sided")
    print(f"  arm a (primary figure): {k}/{n} = {k/n:.3f}  exact 95% Clopper-Pearson [{lo:.3f}, {hi:.3f}]")
    print(f"    vs chance 1/3 (menu = light, mid, heavy; uniform): exact binomial two-sided p = {bt.pvalue:.2e}")
    print("    NOTE chance 1/3 is the wrong baseline: cells born on mid that ignore the list stay on mid. Observed baseline "
          "without the list: below.")
    h = cnt["b"] + cnt["d"]
    lo2, hi2 = cp(h, 32)
    print(f"  hidden list (arms b+d): {h}/32 chose light; CP 95% [{lo2:.3f}, {hi2:.3f}]")
    sh = cnt["a"] + cnt["c"]
    lo3, hi3 = cp(sh, 32)
    print(f"  shown list (arms a+c): {sh}/32 = {sh/32:.3f} CP 95% [{lo3:.3f}, {hi3:.3f}]")
    tab = [[sh, 32 - sh], [h, 32 - h]]
    orr, pf = stats.fisher_exact(tab)
    print(f"  Fisher exact shown vs hidden (cells, treats cells as independent => anti-conservative): p = {pf:.2e}")
    # arm a vs arm b (preregistered contrast S3-c)
    _, pab = stats.fisher_exact([[cnt["a"], 16 - cnt["a"]], [cnt["b"], 16 - cnt["b"]]])
    print(f"  Fisher a vs b (cells): p = {pab:.2e}")
    # run-level
    rs = [sum(c["light0"] for c in sp3[a][r]) / 4 for a in "ac" for r in SP3[a]]
    rh = [sum(c["light0"] for c in sp3[a][r]) / 4 for a in "bd" for r in SP3[a]]
    obs, p, nsp = perm_exact(rs, rh)
    print(f"  run-level exact permutation, per-run proportion, shown (8 runs) vs hidden (8 runs): diff {obs:.3f}, "
          f"p = {p:.2e} over {nsp} splits (min attainable {2/nsp:.2e})")
    ra = [sum(c["light0"] for c in sp3["a"][r]) / 4 for r in SP3["a"]]
    rb = [sum(c["light0"] for c in sp3["b"][r]) / 4 for r in SP3["b"]]
    obs2, p2, nsp2 = perm_exact(ra, rb)
    print(f"  run-level exact permutation arm a vs arm b (4 vs 4 runs): diff {obs2:.3f}, p = {p2:.4f} over {nsp2} splits "
          f"(smallest p possible with 4 vs 4 runs is {2/nsp2:.4f})")
    exc = [(c["run"], c["kit"]) for a in "ac" for r in sp3[a].values() for c in r if not c["light0"]]
    print(f"  shown-arm cells that did NOT move to light at step 0: {len(exc)} -> {exc}")
    nofib_sh = sum(c["light0"] for a in "ac" for r in sp3[a].values() for c in r if c["kit"] != "fibmod")
    nofib_h = sum(c["light0"] for a in "bd" for r in sp3[a].values() for c in r if c["kit"] != "fibmod")
    print(f"  without fibmod: shown {nofib_sh}/24 vs hidden {nofib_h}/24")
    res["sp3"] = {"a": [k, n], "hidden": [h, 32], "shown": [sh, 32], "cp_a": [lo, hi], "binom_p_third": bt.pvalue,
                  "fisher_shown_hidden_p": pf, "runlevel_p_8v8": p, "runlevel_p_ab": p2, "exceptions": exc}
    # SP2 arm f ("second block")
    print("\n  second block: SP2 arm f (s2f1-4), same B1 definition (no `laws` row in SP2 logs; born on mid per TESTS.md SP2 arms)")
    src(ARCH / "s2f1/<kit>/log.jsonl", "first act event carrying `next`; usage.model of first step (born model)")
    f_cells = []
    for r in ["s2f1", "s2f2", "s2f3", "s2f4"]:
        for kit in KITS:
            R = jl(ARCH / r / kit / "log.jsonl")
            models = [x["model"] for x in R if isinstance(x.get("usage"), dict)]
            fn = next((x["next"] for x in R if "act" in x and "step" in x and x.get("next")), None)
            f_cells.append((r, kit, models[0], fn[0] if fn else None, models))
    kf = sum(1 for x in f_cells if x[2] == "mid" and x[3] == "light")
    lof, hif = cp(kf, 16)
    print(f"  SP2 arm f: {kf}/16 chose light at step 0 (CP 95% [{lof:.3f}, {hif:.3f}]); exceptions: "
          f"{[(x[0], x[1]) for x in f_cells if not (x[2]=='mid' and x[3]=='light')]}")
    k2 = sum(1 for x in f_cells if len(x[4]) > 2 and x[4][2] == "light")
    print(f"  (TESTS.md SP2 diag item 2 wording 'on light at step 2': {k2}/16 here)")
    print("  SP2 has NO hidden-list arm. The 'two blocks' repeat the shown-arm rate only; the contrast with hidden prices is "
          "from one block (SP3: b, d).")
    pooled = kf + cnt["a"] + cnt["c"]
    lop, hip = cp(pooled, 48)
    print(f"  pooled price-shown mid-born cells (SP2 f + SP3 a + SP3 c): {pooled}/48 = {pooled/48:.3f} CP [{lop:.3f}, {hip:.3f}]"
          f"  vs hidden 0/32 -> clustered by 12 shown runs and 8 hidden runs")
    res["sp2f"] = [kf, 16]
    res["pooled_shown"] = [pooled, 48]
    # when do hidden cells reach light and why
    forced = chosen = 0
    for a in "bd":
        for r in sp3[a].values():
            for c in r:
                if "light" in c["models"]:
                    i = c["models"].index("light")
                    R = jl(ARCH / c["run"] / c["kit"] / "log.jsonl")
                    # a downshift event precedes the first light step when forced by affordability
                    steps = [(j, x) for j, x in enumerate(R) if isinstance(x.get("usage"), dict)]
                    j0 = steps[i][0]
                    if any(x.get("event") == "downshift" for x in R[:j0]):
                        forced += 1
                    else:
                        chosen += 1
    print(f"  hidden-arm cells that ever thought on light: forced by the affordability rule (downshift event before it) {forced}, "
          f"reached it without a downshift {chosen} (TESTS.md SP3 diagnostics says 16 forced and 8 chose, 24 cells; I count {forced + chosen} cells reaching light "
          f"(b {sum('light' in c['models'] for r in sp3['b'].values() for c in r)}, d {sum('light' in c['models'] for r in sp3['d'].values() for c in r)}); the 16/8 split cannot be reproduced)")
    res["hidden_light_forced"] = [forced, chosen]
    OUT["claim_a"] = res
    return res


# ================================================================ claim (b)
def km_rmst(times, events, tau):
    """Kaplan-Meier restricted mean (area under S(t) on [0, tau]). times in energy spent; events 1 = ended by choice."""
    order = sorted(zip(times, events))
    n = len(order)
    s, last, area, i = 1.0, 0.0, 0.0, 0
    atrisk = n
    while i < n:
        t = order[i][0]
        d = c = 0
        while i < n and order[i][0] == t:
            d += order[i][1]
            c += 1 - order[i][1]
            i += 1
        t_eff = min(t, tau)
        area += s * (t_eff - last)
        last = t_eff
        if t >= tau:
            break
        if atrisk > 0 and d:
            s *= 1 - d / atrisk
        atrisk -= d + c
    if last < tau:
        area += s * (tau - last)
    return area


def claim_b(sp3):
    print("\n" + "=" * 100 + "\nCLAIM (b): hidden prices cost 2.4 to 3.0 times the energy; 'died 7 times against 0'")
    src(ARCH / "s3a1/.ledger.json", "<kit>.spent summed over the 4 kits = energy spent by the run (same rule as sp2.law); "
        "<kit>.state; <kit>/log.jsonl events death, apoptosis, downshift")
    res = {}
    tot = {a: [run_spent(sp3[a][r]) for r in SP3[a]] for a in "abcd"}
    for a in "abcd":
        print(f"  arm {a}: run totals {[round(x, 1) for x in tot[a]]}  arm total {sum(tot[a]):.1f}  (n = 4 runs, 16 cells)")
    # committed text check
    txt = read_text(LAWS / "results/sp3-out.txt")
    for a in "abcd":
        m = re.search(rf"\n  {a}: calls \d+ tokens \d+ \(with cache reads \d+\) usd [\d.]+ energy spent ([\d.]+)", txt)
        if not m or abs(float(m.group(1)) - sum(tot[a])) > 0.06:
            fail(f"arm {a} energy total {sum(tot[a]):.2f} does not match committed sp3-out.txt {m.group(1) if m else None}")
    print("  arm totals match the committed sp3-out.txt 'energy spent' lines (1939.5, 5724.0, 2547.7, 6156.3)")
    rat = lambda x, y: np.mean(x) / np.mean(y)  # noqa: E731
    pairs = {"b/a (sense hidden)": ("b", "a"), "d/c (sense shown)": ("d", "c"), "d/a": ("d", "a"), "b/c": ("b", "c")}
    for name, (h, s) in pairs.items():
        r0 = rat(tot[h], tot[s])
        lo, hi = boot_ci(tot[h], tot[s], rat)
        lr = [x / y for x in tot[h] for y in tot[s]]
        obs, p, nsp = perm_exact(np.log(tot[h]), np.log(tot[s]))
        print(f"  {name}: ratio of arm means {r0:.2f}; bootstrap over runs 95% [{lo:.2f}, {hi:.2f}] (B={BOOT}, 4 vs 4 runs); "
              f"range of the 16 run-pair ratios [{min(lr):.2f}, {max(lr):.2f}]; exact permutation on log run totals p = {p:.4f} "
              f"(min possible {2/nsp:.4f})")
        res[name] = {"ratio": r0, "ci": [lo, hi], "pair_range": [min(lr), max(lr)], "p": p}
    hid = tot["b"] + tot["d"]
    shw = tot["a"] + tot["c"]
    r0 = rat(hid, shw)
    lo, hi = boot_ci(hid, shw, rat)
    obs, p, nsp = perm_exact(np.log(hid), np.log(shw))
    print(f"  hidden (b+d, 8 runs) vs shown (a+c, 8 runs): ratio {r0:.2f}; bootstrap [{lo:.2f}, {hi:.2f}]; exact permutation p = "
          f"{p:.2e} over {nsp} splits")
    res["hidden_vs_shown"] = {"ratio": r0, "ci": [lo, hi], "p": p}
    # spend per cell and budget
    cells = [c for a in "abcd" for r in sp3[a].values() for c in r]
    for a in "abcd":
        cs = [c for r in sp3[a].values() for c in r]
        print(f"    arm {a}: spent per cell mean {np.mean([c['spent'] for c in cs]):.1f} (endowment 400 + gifts received); "
              f"cells with spent >= 340: {sum(c['spent'] >= 340 for c in cs)}/16; pre-assay spend per cell {np.mean([c['pre'] for c in cs]):.1f}, "
              f"post-assay {np.mean([c['post'] for c in cs]):.1f}; unspent energy at end (gave+left) median "
              f"{np.median([c['left'] for c in cs]):.1f}")
    # deaths
    print("\n  deaths")
    dead_ev = {a: sum(c["death"] for r in sp3[a].values() for c in r) for a in "abcd"}
    dead_state = {a: sum(c["state"] == "dead" for r in sp3[a].values() for c in r) for a in "abcd"}
    apop = {a: sum(c["apop"] for r in sp3[a].values() for c in r) for a in "abcd"}
    print(f"  `death` events by arm {dead_ev}; ledger state 'dead' {dead_state}; `apoptosis` (ended after repeated empty replies) {apop}")
    h7, s0 = dead_ev["b"] + dead_ev["d"], dead_ev["a"] + dead_ev["c"]
    orr, pf = stats.fisher_exact([[h7, 32 - h7], [s0, 32 - s0]])
    print(f"  cells: hidden {h7}/32 vs shown {s0}/32; Fisher exact two-sided p = {pf:.4f} (cells treated as independent)")
    loh, hih = cp(h7, 32)
    print(f"    hidden death rate {h7/32:.3f} CP 95% [{loh:.3f}, {hih:.3f}]; shown 0/32 CP upper {cp(0,32)[1]:.3f}")
    h9, s9 = dead_state["b"] + dead_state["d"], dead_state["a"] + dead_state["c"]
    _, pf9 = stats.fisher_exact([[h9, 32 - h9], [s9, 32 - s9]])
    print(f"  with apoptosis counted as death (ledger state dead): hidden {h9}/32 vs shown {s9}/32, Fisher p = {pf9:.4f}")
    runs_h = sum(any(c["death"] for c in sp3[a][r]) for a in "bd" for r in SP3[a])
    runs_s = sum(any(c["death"] for c in sp3[a][r]) for a in "ac" for r in SP3[a])
    _, pr = stats.fisher_exact([[runs_h, 8 - runs_h], [runs_s, 8 - runs_s]])
    print(f"  runs with at least one death event: hidden {runs_h}/8 vs shown {runs_s}/8; Fisher exact p = {pr:.4f} (run is the unit)")
    ph, ps = cp(runs_h, 8), cp(runs_s, 8)
    print(f"    CP 95%: hidden [{ph[0]:.3f}, {ph[1]:.3f}], shown [{ps[0]:.3f}, {ps[1]:.3f}]")
    print("  MECHANICAL: a death is energy reaching zero. Shown-arm cells rest with 200 to 1300 unspent (median "
          f"{np.median([c['left'] for a in 'ac' for r in sp3[a].values() for c in r]):.0f}), so they cannot die. Deaths are the "
          "same phenomenon as the energy gap (cells that stay on mid burn the endowment), not a second finding.")
    res["deaths"] = {"cells": [h7, s0], "fisher_p": pf, "state_dead": [h9, s9], "runs": [runs_h, runs_s], "runs_p": pr}

    # ---- part 4: mechanical component
    print("\n  TRUNCATION / CENSORING (task item 4)")
    print("  The no-credit rule cuts a cell's spend at its available energy (400 + gifts). A truncated cell's measured spend is a "
          "LOWER bound on what it would have spent, so truncation shrinks the hidden-arm measured gap; it cannot inflate it.")
    print("  Definitions (per cell, from ledger + log): TRUNCATED = death or apoptosis event, or unspent energy at its end "
          "(ledger gave + e) below THR. Sensitivity THR in {50, 100, 150}.")
    out4 = {}
    for thr in (50, 100, 150):
        d = {}
        for a in "abcd":
            cs = [c for r in sp3[a].values() for c in r]
            tr = [c for c in cs if c["death"] or c["apop"] or c["left"] < thr]
            nt = [c for c in cs if not (c["death"] or c["apop"] or c["left"] < thr)]
            d[a] = {"n_trunc": len(tr), "n_free": len(nt), "free_spent": [c["spent"] for c in nt], "free_cells": nt}
        # cell-level ratio of means with run-cluster bootstrap
        def ratio(hset, sset):
            hv = [c["spent"] for a in hset for c in d[a]["free_cells"]]
            sv = [c["spent"] for a in sset for c in d[a]["free_cells"]]
            return np.mean(hv) / np.mean(sv) if hv and sv else float("nan"), len(hv), len(sv)
        r_all, nh, ns = ratio("bd", "ac")
        # cluster bootstrap: resample runs within arm-group, keep cells of run that survive the filter
        rng = np.random.default_rng(SEED)
        runs_h_ = [(a, r) for a in "bd" for r in SP3[a]]
        runs_s_ = [(a, r) for a in "ac" for r in SP3[a]]
        def cells_free(a, r):
            return [c["spent"] for c in sp3[a][r] if not (c["death"] or c["apop"] or c["left"] < thr)]
        vals = []
        for _ in range(8000):
            hv = [x for i in rng.integers(0, len(runs_h_), len(runs_h_)) for x in cells_free(*runs_h_[i])]
            sv = [x for i in rng.integers(0, len(runs_s_), len(runs_s_)) for x in cells_free(*runs_s_[i])]
            if hv and sv:
                vals.append(np.mean(hv) / np.mean(sv))
        lo, hi = np.percentile(vals, [2.5, 97.5])
        cnt_tr = {a: d[a]["n_trunc"] for a in "abcd"}
        print(f"    THR {thr}: truncated cells by arm {cnt_tr}; among NON-truncated cells, mean spend hidden {np.mean([c['spent'] for a in 'bd' for c in d[a]['free_cells']]):.1f} (n={nh}) "
              f"vs shown {np.mean([c['spent'] for a in 'ac' for c in d[a]['free_cells']]):.1f} (n={ns}); ratio {r_all:.2f}, run-cluster bootstrap 95% [{lo:.2f}, {hi:.2f}]")
        out4[thr] = {"trunc": cnt_tr, "ratio": r_all, "ci": [float(lo), float(hi)], "n": [nh, ns]}
    print("    (conditioning on 'not truncated' selects hidden cells that quit early; this is a sensitivity bound, not an unbiased estimate)")
    # pairwise (the 2.4 and 3.0 are b/a and d/c) among non-truncated cells, THR 100
    for h_, s_ in (("b", "a"), ("d", "c")):
        def free(a, thr=100):
            return [c["spent"] for r in sp3[a].values() for c in r if not (c["death"] or c["apop"] or c["left"] < thr)]
        fh, fs = free(h_), free(s_)
        print(f"    pairwise among non-truncated cells (THR 100): {h_}/{s_} = {np.mean(fh):.1f} (n={len(fh)}) / {np.mean(fs):.1f} (n={len(fs)}) = {np.mean(fh)/np.mean(fs):.2f}  (measured run-total ratio {np.mean(tot[h_])/np.mean(tot[s_]):.2f})")
    # pre/post decomposition
    gap = {}
    for g, aa in (("hidden", "bd"), ("shown", "ac")):
        cs = [c for a in aa for r in sp3[a].values() for c in r]
        gap[g] = (np.mean([c["pre"] for c in cs]), np.mean([c["post"] for c in cs]))
    dpre = gap["hidden"][0] - gap["shown"][0]
    dpost = gap["hidden"][1] - gap["shown"][1]
    print(f"    step-cost decomposition per cell (sum of log `cost` before / after the first assay): hidden {gap['hidden'][0]:.1f} / "
          f"{gap['hidden'][1]:.1f}, shown {gap['shown'][0]:.1f} / {gap['shown'][1]:.1f}. "
          f"Gap before first assay {dpre:+.1f}, after {dpost:+.1f} -> {100*dpre/(dpre+dpost):.0f}% of the per-cell gap is spent before the first assay "
          "(the mid-model steps: the behaviour itself, not a side effect of the death rule)")
    # KM, truncated treated as censored
    for thr in (100,):
        out = {}
        for g, aa in (("hidden", "bd"), ("shown", "ac")):
            cs = [c for a in aa for r in sp3[a].values() for c in r]
            times = [c["spent"] for c in cs]
            ev = [0 if (c["death"] or c["apop"] or c["left"] < thr) else 1 for c in cs]
            out[g] = (times, ev)
        tau = 450.0
        rm_h = km_rmst(*out["hidden"], tau)
        rm_s = km_rmst(*out["shown"], tau)
        rng = np.random.default_rng(SEED)
        runs_g = {g: [[(c["spent"], 0 if (c["death"] or c["apop"] or c["left"] < thr) else 1) for c in sp3[a][r]]
                      for a in aa for r in SP3[a]] for g, aa in (("hidden", "bd"), ("shown", "ac"))}
        vals = []
        for _ in range(8000):
            def samp(g):
                lst = runs_g[g]
                cs = [x for i in rng.integers(0, len(lst), len(lst)) for x in lst[i]]
                return km_rmst([x[0] for x in cs], [x[1] for x in cs], tau)
            vals.append(samp("hidden") / samp("shown"))
        lo, hi = np.percentile(vals, [2.5, 97.5])
        raw = np.mean(out["hidden"][0]) / np.mean(out["shown"][0])
        print(f"    censored view (THR {thr}, truncated cells right-censored at the energy they had spent; event = ended by choice with energy left; "
              f"Kaplan-Meier restricted mean to {tau:.0f}): hidden {rm_h:.1f} vs shown {rm_s:.1f}, ratio {rm_h/rm_s:.2f}, run-cluster bootstrap 95% [{lo:.2f}, {hi:.2f}] "
              f"(plain per-cell means ratio {raw:.2f})")
        out4["km"] = {"hidden": rm_h, "shown": rm_s, "ratio": rm_h / rm_s, "ci": [float(lo), float(hi)]}
    # runs not truncated by death
    rows = []
    for a in "bd":
        for r in SP3[a]:
            dd = sum(c["death"] + c["apop"] for c in sp3[a][r])
            rows.append((r, dd, run_spent(sp3[a][r])))
    print("    runs with no death or apoptosis event (spent):", [(r, round(s, 1)) for r, dd, s in rows if dd == 0] or "none",
          " | runs with one or more:", [(r, dd, round(s, 1)) for r, dd, s in rows if dd > 0])
    free_runs = [s for r, dd, s in rows if dd == 0]
    if free_runs:
        base = np.mean(tot["a"] + tot["c"])
        print(f"      those untruncated hidden runs average {np.mean(free_runs):.1f} against {base:.1f} for the 8 shown runs "
              f"(ratio {np.mean(free_runs)/base:.2f}, n = {len(free_runs)} run(s), no interval possible)")
    OUT["claim_b"] = {"runs": tot, "res": {k: v for k, v in res.items()}, "trunc": {str(k): v for k, v in out4.items()},
                      "gap_pre_post": {"pre": dpre, "post": dpost}}
    return res


# ================================================================ claim (c) and reach
def claim_c(sp3, rel):
    print("\n" + "=" * 100 + "\nCLAIM (c): score against best known body (sense) raises reach")
    src(LAWS / "results/sp3-ref.json", "rel (final body / fixed reference body) per (run, kit); O1 = median over the 4 kits per run, "
        "arm value = mean of 4 run medians (sp2.py definition)")
    res = {}
    O1 = {a: [o1(rel, r) for r in SP3[a]] for a in "abcd"}
    O1nf = {a: [o1(rel, r, ("compress", "csvsum", "maze")) for r in SP3[a]] for a in "abcd"}
    for a in "abcd":
        print(f"  arm {a}: run O1 {[round(x, 3) for x in O1[a]]} mean {np.mean(O1[a]):.4f} | without fibmod {[round(x, 3) for x in O1nf[a]]} mean {np.mean(O1nf[a]):.4f}")
    committed = {"a": 1.4839, "b": 1.8765, "c": 2.0266, "d": 1.6539}
    for a in "abcd":
        if abs(np.mean(O1[a]) - committed[a]) > 6e-4:
            fail(f"O1 arm {a} {np.mean(O1[a]):.4f} != committed {committed[a]}")
    print("  O1 arm means match the committed sp3-out.txt (1.4839, 1.8765, 2.0266, 1.6539)")
    # per-kit
    print("  per-kit mean rel by arm:")
    for k in KITS:
        print("    " + k.ljust(9) + "  ".join(f"{a}: {np.mean([rel.get((r, k), 0) for r in SP3[a]]):.3f}" for a in "abcd")
              + "   run values c " + str([round(rel.get((r, k), 0), 2) for r in SP3["c"]]) + "  a " + str([round(rel.get((r, k), 0), 2) for r in SP3["a"]]))
    d = np.mean(O1["c"]) - np.mean(O1["a"])
    print(f"\n  (1) the test TESTS.md committed to for the primary guess S3-i: decision rule 'c above a by 0.10 or more on O1' -> "
          f"{d:+.4f} >= 0.10 : HELD. It is a threshold on a point estimate, with no sampling error attached.")
    print("      The committed significance report is sp2.perm (cell medians shuffled between arms, 5000 shuffles, seed 0, two-sided):")
    cellsA = [rel.get((r, k), 0.0) for r in SP3["a"] for k in KITS]
    cellsC = [rel.get((r, k), 0.0) for r in SP3["c"] for k in KITS]

    def sp2perm(a, b, shuffles=5000, seed=0):
        rng = random.Random(seed)
        obs = statistics.median(a) - statistics.median(b)
        pool, n, hit = a + b, len(a), 0
        for _ in range(shuffles):
            rng.shuffle(pool)
            if abs(statistics.median(pool[:n]) - statistics.median(pool[n:])) >= abs(obs) - 1e-12:
                hit += 1
        return round(obs, 4), round((hit + 1) / (shuffles + 1), 4)
    ob, pc = sp2perm(list(cellsA), list(cellsC))
    print(f"      a vs c, 16 cells vs 16 cells, difference of medians {ob:+.4f}, p = {pc} (committed text: 0.3619). Overstates n: 4 cells share a run.")
    if abs(pc - 0.3619) > 0.002:
        print("      WARNING: does not reproduce the committed 0.3619 exactly")
    nfa = [rel.get((r, k), 0.0) for r in SP3["a"] for k in KITS if k != "fibmod"]
    nfc = [rel.get((r, k), 0.0) for r in SP3["c"] for k in KITS if k != "fibmod"]
    ob2, pc2 = sp2perm(list(nfa), list(nfc))
    print(f"      same test without fibmod (12 vs 12 cells): difference of medians {ob2:+.4f}, p = {pc2}")
    print("  (2) run-level exact permutation on O1 (the run is the replicate), a vs c, 4 vs 4 runs:")
    obs, p, nsp = perm_exact(O1["c"], O1["a"])
    lo, hi = boot_ci(O1["c"], O1["a"], lambda x, y: np.mean(x) - np.mean(y))
    print(f"      with all 4 kits: c - a = {obs:+.4f}; exact p = {p:.4f} ({nsp} splits; complete separation gives the minimum 2/70 = 0.0286); "
          f"bootstrap over runs 95% [{lo:+.3f}, {hi:+.3f}]")
    obs_n, p_n, _ = perm_exact(O1nf["c"], O1nf["a"])
    lo_n, hi_n = boot_ci(O1nf["c"], O1nf["a"], lambda x, y: np.mean(x) - np.mean(y))
    print(f"      WITHOUT fibmod (median of compress, csvsum, maze): c - a = {obs_n:+.4f}; exact p = {p_n:.4f}; bootstrap 95% [{lo_n:+.3f}, {hi_n:+.3f}]")
    # fibmod only
    fa = [rel.get((r, "fibmod"), 0) for r in SP3["a"]]
    fc = [rel.get((r, "fibmod"), 0) for r in SP3["c"]]
    obs_f, p_f, _ = perm_exact(fc, fa)
    lo_f, hi_f = boot_ci(fc, fa, lambda x, y: np.mean(x) - np.mean(y))
    print(f"      fibmod alone: c - a = {obs_f:+.3f}; exact p = {p_f:.4f}; bootstrap 95% [{lo_f:+.2f}, {hi_f:+.2f}]; c runs {[round(x,2) for x in fc]}, a runs {[round(x,2) for x in fa]}")
    other = {}
    for k in ("compress", "csvsum", "maze"):
        xa = [rel.get((r, k), 0) for r in SP3["a"]]
        xc = [rel.get((r, k), 0) for r in SP3["c"]]
        ob_k, p_k, _ = perm_exact(xc, xa)
        other[k] = (ob_k, p_k)
        print(f"      {k}: c - a = {ob_k:+.3f}, exact p = {p_k:.4f}")
    print("  (3) main effect of showing sense, both price conditions pooled (c+d vs a+b, 8 vs 8 runs):")
    sa = O1["c"] + O1["d"]
    sb = O1["a"] + O1["b"]
    obs_m, p_m, nspm = perm_exact(sa, sb)
    lo_m, hi_m = boot_ci(sa, sb, lambda x, y: np.mean(x) - np.mean(y))
    print(f"      all 4 kits: {obs_m:+.4f}; exact p = {p_m:.4f} ({nspm} splits); bootstrap 95% [{lo_m:+.3f}, {hi_m:+.3f}]")
    sa2 = O1nf["c"] + O1nf["d"]
    sb2 = O1nf["a"] + O1nf["b"]
    obs_m2, p_m2, _ = perm_exact(sa2, sb2)
    lo_m2, hi_m2 = boot_ci(sa2, sb2, lambda x, y: np.mean(x) - np.mean(y))
    print(f"      without fibmod: {obs_m2:+.4f}; exact p = {p_m2:.4f}; bootstrap 95% [{lo_m2:+.3f}, {hi_m2:+.3f}]")
    # d vs b: sense with price hidden
    obs_db, p_db, _ = perm_exact(O1["d"], O1["b"])
    print(f"      sense effect when prices hidden (d - b): {obs_db:+.4f}, exact p = {p_db:.4f} (opposite sign: hidden-price arms are dominated by deaths)")
    # price effect on reach
    obs_pb, p_pb, _ = perm_exact(O1["b"], O1["a"])
    lo_pb, hi_pb = boot_ci(O1["b"], O1["a"], lambda x, y: np.mean(x) - np.mean(y))
    print(f"  Price hidden vs shown on reach (b - a; README says hiding 'did not buy better work'): {obs_pb:+.4f}, exact p = {p_pb:.4f}, bootstrap [{lo_pb:+.3f}, {hi_pb:+.3f}]; "
          f"without fibmod {np.mean(O1nf['b'])-np.mean(O1nf['a']):+.4f}")
    obs_pb2, p_pb2, _ = perm_exact(O1nf["b"], O1nf["a"])
    print(f"      without fibmod exact p = {p_pb2:.4f}")
    res.update({"O1": O1, "O1nf": O1nf, "c_minus_a": d, "cell_perm_p": pc, "cell_perm_p_nofib": pc2,
                "run_perm": {"obs": obs, "p": p, "ci": [lo, hi]},
                "run_perm_nofib": {"obs": obs_n, "p": p_n, "ci": [lo_n, hi_n]},
                "fibmod_only": {"obs": obs_f, "p": p_f}, "main_effect": {"obs": obs_m, "p": p_m, "ci": [lo_m, hi_m]},
                "main_effect_nofib": {"obs": obs_m2, "p": p_m2, "ci": [lo_m2, hi_m2]},
                "b_minus_a": {"obs": obs_pb, "p": p_pb, "ci": [lo_pb, hi_pb], "p_nofib": p_pb2},
                "other_kits": {k: list(v) for k, v in other.items()}})
    # SD stats used in power
    print("\n  run-level SD of O1 (used by power_sim.py): " + ", ".join(f"{a} {np.std(O1[a], ddof=1):.3f}" for a in "abcd") +
          f" | without fibmod: " + ", ".join(f"{a} {np.std(O1nf[a], ddof=1):.3f}" for a in "abcd"))
    OUT["claim_c"] = res
    return res


# ================================================================ claim (d)
def tokens_run(run, parts):
    t = 0
    for d in parts:
        p = ARCH / run / d / "log.jsonl"
        if not p.exists():
            continue
        for e in jl(p):
            u = e.get("usage")
            if isinstance(u, dict):
                t += (u.get("inp") or 0) + (u.get("out") or 0) + (u.get("cw") or 0)
    return t


def spent_run_all(run):
    led = jf(ARCH / run / ".ledger.json")
    return sum(v.get("spent", 0) for k, v in led.items() if "/" not in k)


def claim_d():
    print("\n" + "=" * 100 + "\nCLAIM (d): a stem cell that feeds others added cost and no reach (two blocks)")
    res = {}
    parts = list(KITS) + ["stem"]
    # SP2
    rel2 = rel_table(LAWS / "results/sp2-ref.json")
    src(LAWS / "results/sp2-ref.json", "rel per (run, kit)")
    src(ARCH / "s2f1/.ledger.json", "spent (keys without '/'); tokens = usage.inp+out+cw summed over <kit> and stem logs")
    arms = {"f": [f"s2f{i}" for i in "1234"], "s": [f"s2s{i}" for i in "1234"], "m": [f"s2m{i}" for i in "1234"]}
    D = {}
    for a, runs in arms.items():
        D[a] = {"O1": [o1(rel2, r) for r in runs], "tok": [tokens_run(r, parts) for r in runs], "en": [spent_run_all(r) for r in runs],
                "O1nf": [o1(rel2, r, ("compress", "csvsum", "maze")) for r in runs]}
        print(f"  SP2 arm {a} (4 runs): O1 {[round(x,3) for x in D[a]['O1']]} mean {np.mean(D[a]['O1']):.4f}; tokens {D[a]['tok']}; energy {[round(x,1) for x in D[a]['en']]}")
    if abs(np.mean(D["f"]["O1"]) - 1.5775) > 6e-4 or abs(np.mean(D["s"]["O1"]) - 1.4713) > 6e-4:
        fail("SP2 O1 does not match committed 1.5775 / 1.4713")
    print("  SP2 O1 matches committed (f 1.5775, s 1.4713, m 1.5461)")
    obs, p, nsp = perm_exact(D["s"]["O1"], D["f"]["O1"])
    lo, hi = boot_ci(D["s"]["O1"], D["f"]["O1"], lambda x, y: np.mean(x) - np.mean(y))
    print(f"  reach, stem - flat (O1, run-level): {obs:+.4f}; exact p = {p:.4f}; bootstrap 95% [{lo:+.3f}, {hi:+.3f}]  -> interval covers a benefit of up to {hi:+.2f}")
    res["sp2_reach"] = {"diff": obs, "p": p, "ci": [lo, hi]}
    obs_n, p_n, _ = perm_exact(D["s"]["O1nf"], D["f"]["O1nf"])
    print(f"  reach without fibmod: {obs_n:+.4f}; exact p = {p_n:.4f}")
    rt = lambda x, y: np.mean(x) / np.mean(y)  # noqa: E731
    r0 = rt(D["s"]["tok"], D["f"]["tok"])
    lo, hi = boot_ci(D["s"]["tok"], D["f"]["tok"], rt)
    obs_t, p_t, _ = perm_exact(np.log(D["s"]["tok"]), np.log(D["f"]["tok"]))
    print(f"  cost, tokens stem/flat: {r0:.2f}; bootstrap over runs 95% [{lo:.2f}, {hi:.2f}]; exact permutation on log tokens p = {p_t:.4f} (committed text: 1.61)")
    res["sp2_tokens"] = {"ratio": r0, "ci": [lo, hi], "p": p_t}
    r1 = rt(D["s"]["en"], D["f"]["en"])
    lo1, hi1 = boot_ci(D["s"]["en"], D["f"]["en"], rt)
    obs_e, p_e, _ = perm_exact(np.log(D["s"]["en"]), np.log(D["f"]["en"]))
    print(f"  cost, energy stem/flat: {r1:.2f}; bootstrap [{lo1:.2f}, {hi1:.2f}]; exact permutation p = {p_e:.4f} (committed text: 1.28)")
    res["sp2_energy"] = {"ratio": r1, "ci": [lo1, hi1], "p": p_e}
    # SP1
    rel1 = rel_table(LAWS / "results/sp1-ref.json")
    src(LAWS / "results/sp1-ref.json", "rel per (run, kit)")
    flat1, stem1 = ["fl1", "fl2"], ["sp1", "sp2"]
    o_f = [o1(rel1, r) for r in flat1]
    o_s = [o1(rel1, r) for r in stem1]
    t_f = [tokens_run(r, parts) for r in flat1]
    t_s = [tokens_run(r, parts) for r in stem1]
    e_f = [spent_run_all(r) for r in flat1]
    e_s = [spent_run_all(r) for r in stem1]
    print(f"  SP1 (2 runs per arm): O1 flat {[round(x,3) for x in o_f]} mean {np.mean(o_f):.3f}; stem {[round(x,3) for x in o_s]} mean {np.mean(o_s):.3f} (committed 1.372 / 1.352)")
    print(f"      tokens stem/flat {np.mean(t_s)/np.mean(t_f):.2f} (committed 1.70); energy {np.mean(e_s)/np.mean(e_f):.2f} (committed 1.65). With 2 vs 2 runs the smallest possible two-sided permutation p is 0.33: no test is possible.")
    res["sp1"] = {"O1": [o_f, o_s], "tok_ratio": np.mean(t_s) / np.mean(t_f), "en_ratio": np.mean(e_s) / np.mean(e_f)}
    # pooled
    pooled_s = D["s"]["O1"] + o_s
    pooled_f = D["f"]["O1"] + o_f
    obs_p, p_p, _ = perm_exact(pooled_s, pooled_f)
    lo_p, hi_p = boot_ci(pooled_s, pooled_f, lambda x, y: np.mean(x) - np.mean(y))
    print(f"  pooled SP1+SP2 reach (6 stem vs 6 flat runs; different design details, same reference metric): {obs_p:+.4f}, exact p = {p_p:.4f}, bootstrap [{lo_p:+.3f}, {hi_p:+.3f}]")
    tok_s = D["s"]["tok"] + t_s
    tok_f = D["f"]["tok"] + t_f
    obs_pt, p_pt, _ = perm_exact(np.log(tok_s), np.log(tok_f))
    lo_pt, hi_pt = boot_ci(tok_s, tok_f, rt)
    print(f"  pooled tokens stem/flat {rt(tok_s, tok_f):.2f}, bootstrap [{lo_pt:.2f}, {hi_pt:.2f}], exact p = {p_pt:.4f} (6 vs 6 runs)")
    res["pooled"] = {"reach": [obs_p, p_p, lo_p, hi_p], "tok": [rt(tok_s, tok_f), p_pt, lo_pt, hi_pt]}
    print("  NOTE SP1 and SP2 differ: SP1 stem arm births on light with 150-200 energy; the SP1 'gain' metric was found invalid and replaced by rel. Not independent confirmations of one pre-planned test: SP2 was written after SP1 to repeat it.")
    OUT["claim_d"] = res
    return res


# ================================================================ claim (e)
def claim_e():
    print("\n" + "=" * 100 + "\nCLAIM (e): heredity saved energy and did not compound (L1, 3 runs per arm)")
    src(ARCH / "l1h1/lineage.jsonl", "event 'gen' rows: spent, cells, states, took, gain, store; 'start' row")
    src(LAWS / "results/l1-ref.json", "rel per (run, kit) of final germline body")
    rel = rel_table(LAWS / "results/l1-ref.json")
    arms = {"h": ["l1h1", "l1h2", "l1h3"], "b": ["l1b1", "l1b2", "l1b3"]}
    R = {}
    for a, runs in arms.items():
        R[a] = {"spent": [], "O1": [], "deaths": [], "cells": [], "idle": [], "late": [], "late_takes": [], "lineages": 0, "last_gen_cells": 0}
        for run in runs:
            rows = jl(ARCH / run / "lineage.jsonl")
            start = next(r for r in rows if r.get("event") == "start")
            gens = [r for r in rows if r.get("event") == "gen"]
            R[a]["spent"].append(sum(g["spent"] for g in gens))
            R[a]["O1"].append(o1(rel, run))
            R[a]["deaths"].append(sum(1 for g in gens for c in g["cells"] if g["states"].get(c) == "dead"))
            R[a]["cells"].append(sum(len(g["cells"]) for g in gens))
            idle = late = 0
            for g in gens:
                if g["gen"] >= 1:
                    for c in g["cells"]:
                        late += 1
                        ev = jl(ARCH / run / c / "log.jsonl") if (ARCH / run / c / "log.jsonl").exists() else []
                        acts = [(e.get("act") or {}).get("do") for e in ev if e.get("act")]
                        if not any(x in ("write", "variants", "divide") for x in acts):
                            idle += 1
            R[a]["idle"].append(idle)
            R[a]["late"].append(late)
            R[a]["late_takes"].append(sum(1 for g in gens if g["gen"] >= 1 and g.get("took")))
            R[a]["last_gen_cells"] += sum(len(g["cells"]) for g in gens if g["gen"] == start["gens"] - 1)
            # lineages replacing germline after gen 0
        wl = 0
        for run in runs:
            rows = jl(ARCH / run / "lineage.jsonl")
            gens = [r for r in rows if r.get("event") == "gen"]
            for k in KITS:
                if any(g["kit"] == k and g["gen"] >= 1 and g.get("took") for g in gens):
                    wl += 1
        R[a]["lineages_replaced"] = wl
    for a in "hb":
        print(f"  arm {a}: run energy spent {[round(x,1) for x in R[a]['spent']]} (total {sum(R[a]['spent']):.1f}); O1 {[round(x,3) for x in R[a]['O1']]}; deaths per run {R[a]['deaths']}; "
              f"cells per run {R[a]['cells']}; later-generation cells with no write/variants/divide {sum(R[a]['idle'])}/{sum(R[a]['late'])}; lineages that replaced germline after gen 0 {R[a]['lineages_replaced']}/12; cells born in last generation {R[a]['last_gen_cells']}/24")
    if abs(sum(R["h"]["spent"]) - 14152.5) > 0.2 or abs(sum(R["b"]["spent"]) - 20642.6) > 0.2:
        fail("L1 energy totals do not match committed l1-out.txt")
    print("  totals match committed l1-out.txt (14152.5, 20642.6); committed 'idle 65 of 70' and 'replaced 3 of 12' recomputed above")
    rt = lambda x, y: np.mean(x) / np.mean(y)  # noqa: E731
    r0 = rt(R["h"]["spent"], R["b"]["spent"])
    lo, hi = boot_ci(R["h"]["spent"], R["b"]["spent"], rt)
    obs, p, nsp = perm_exact(np.log(R["h"]["spent"]), np.log(R["b"]["spent"]))
    print(f"  energy, heredity / blank: {r0:.3f} (saving {100*(1-r0):.0f}%); bootstrap over 3 vs 3 runs 95% [{lo:.2f}, {hi:.2f}]; exact permutation p = {p:.3f} over {nsp} splits "
          f"(with 3 vs 3 runs the smallest two-sided p is {2/nsp:.2f}, so no test can reach 0.05)")
    rng = [(x / y) for x in R["h"]["spent"] for y in R["b"]["spent"]]
    print(f"      the 9 run-pair ratios range {min(rng):.2f} to {max(rng):.2f}")
    obs_o, p_o, _ = perm_exact(R["h"]["O1"], R["b"]["O1"])
    lo_o, hi_o = boot_ci(R["h"]["O1"], R["b"]["O1"], lambda x, y: np.mean(x) - np.mean(y))
    print(f"  reach, heredity - blank (O1): {obs_o:+.4f}; exact p = {p_o:.3f}; bootstrap 95% [{lo_o:+.2f}, {hi_o:+.2f}] -> cannot exclude differences of +-0.2 in either direction")
    d_h, d_b = sum(R["h"]["deaths"]), sum(R["b"]["deaths"])
    n_h, n_b = sum(R["h"]["cells"]), sum(R["b"]["cells"])
    _, pdd = stats.fisher_exact([[d_h, n_h - d_h], [d_b, n_b - d_b]])
    print(f"  deaths: h {d_h}/{n_h} cells vs b {d_b}/{n_b}; Fisher (cells) p = {pdd:.4f}; per run h {R['h']['deaths']}, b {R['b']['deaths']}")
    wl_h, wl_b = R["h"]["lineages_replaced"], R["b"]["lineages_replaced"]
    print(f"  'did not compound': h {wl_h}/12 lineages replaced the germline after gen 0 (b {wl_b}/12). Fisher h vs b p = {stats.fisher_exact([[wl_h,12-wl_h],[wl_b,12-wl_b]])[1]:.2f}. "
          f"Idle heirs {sum(R['h']['idle'])}/{sum(R['h']['late'])} (CP 95% [{cp(sum(R['h']['idle']), sum(R['h']['late']))[0]:.2f}, {cp(sum(R['h']['idle']), sum(R['h']['late']))[1]:.2f}]; heirs within a lineage are not independent)")
    print("  CENSORING in L1: the blank arm's stores ran dry; it funded " f"{R['b']['last_gen_cells']}/24 last-generation births against {R['h']['last_gen_cells']}/24 for heredity, so blank's spend is also capped by the store, "
          "and heredity's smaller spend is mostly heirs that rest at once (65/70 did nothing) rather than cheaper search.")
    OUT["claim_e"] = {"R": {a: {k: v for k, v in R[a].items()} for a in R}, "ratio": r0, "ci": [lo, hi], "p": p, "O1": [obs_o, p_o, lo_o, hi_o]}
    return R


# ================================================================ claim (f)
def claim_f():
    print("\n" + "=" * 100 + "\nCLAIM (f): any claim in openai-cells-blitz that the laws replicate or fail to replicate on a second model family")
    terms = ["price list", "price display", "price shown", "sense", "energy", "heredity", "stem cell", "lineage", "VITALS", "metab", "colony law", "laws"]
    files = [p for p in sorted(BLITZ.glob("*.md")) + [BLITZ / "harness.py", BLITZ / "analyze_replay.py", BLITZ / "replay.py"]]
    hits = {}
    for p in files:
        t = read_text(p)
        for term in terms:
            n = len(re.findall(re.escape(term), t, flags=re.I))
            if n:
                hits.setdefault(p.name, {})[term] = n
    print("  case-insensitive term counts in the blitz markdown and scripts (price/sense/energy/heredity/stem/lineage/metab/laws):", hits or "NONE")
    for p in sorted(BLITZ.glob("PREREG*.md")):
        t = read_text(p)
        hs = re.findall(r"^- (H-[A-Z0-9-]+)", t, flags=re.M)
        print(f"  {p.name}: hypotheses {len(hs)} {hs}")
    nl_hits = {}
    for p in sorted(NL.glob("*.md")):
        t = read_text(p)
        for term in terms[:6]:
            n = len(re.findall(re.escape(term), t, flags=re.I))
            if n:
                nl_hits.setdefault(p.name, {})[term] = n
    print("  no-language-colony-2026-11-12 same terms:", nl_hits or "NONE")
    # the instrument: counts that CAN be recomputed
    ev = []
    cells = set()
    for p in sorted((BLITZ / "logs").glob("*.jsonl")):
        if p.name == "usage.jsonl":
            continue
        try:
            rows = jl(p)
        except Exception:
            continue
        cells.add(p.stem)
        for r in rows:
            ev.append((p.stem, r))
    kinds = {}
    for _, r in ev:
        k = r.get("event") or r.get("type") or r.get("kind")
        kinds[k] = kinds.get(k, 0) + 1
    print("  log event kinds in blitz logs (top):", sorted(kinds.items(), key=lambda kv: -kv[1])[:10], "| log files", len(cells))
    n_tc = sum(1 for _, r in ev if r.get("kind") == "tool_call" and r.get("name") == "variants")
    n_vr = sum(1 for _, r in ev if r.get("kind") == "variants_result")
    n_ad = sum(1 for _, r in ev if r.get("kind") == "variants_result" and r.get("adopted") is not None)
    n_cells = len({c for c, r in ev if r.get("kind") == "variants_result" and r.get("adopted") is not None})
    n_calls = sum(1 for _, r in ev if r.get("kind") == "usage")
    print(f"  recomputed from logs: model calls {n_calls}, variants tool calls {n_tc}, variants_result {n_vr}, reported selections (adopted not null) {n_ad} in {n_cells} cells "
          f"(RECONCILIATION-2026-11-12.md: 1,180 / 111 / 38 / 37 cells; 0 of 38 had the winner on disk under the old harness)")
    if (n_calls, n_tc, n_ad, n_cells) != (1180, 111, 38, 37):
        fail("blitz counts do not match RECONCILIATION-2026-11-12.md")
    # retention under the OLD harness: the surviving body was always the last candidate, so a selection is retained only if adopted == last index
    ret = tot_sel = 0
    last_nv = {}
    for c, r in ev:
        if r.get("kind") == "tool_call" and r.get("name") == "variants":
            last_nv[c] = len((r.get("args") or {}).get("versions") or [])
        if r.get("kind") == "variants_result" and r.get("adopted") is not None:
            tot_sel += 1
            ret += int(r["adopted"] == last_nv.get(c, -1) - 1)
    print(f"  reported selections whose adopted index equals the last candidate (the only body the old harness left on disk): {ret} of {tot_sel} "
          "(arithmetic on the raw events, as in RECONCILIATION-2026-11-12.md)")
    src(BLITZ / "logs/*.jsonl", "kind == 'usage' | 'tool_call' (name == 'variants', args.versions) | 'variants_result' (adopted)")
    print("  VERDICT: no price, sense, energy, stem or heredity condition exists in the blitz harness or any registration file. The blitz tests one thing "
          "(adherence to the `variants` selection channel on `compress`). It makes no replicate or fail-to-replicate claim about the laws, and could not.")
    OUT["claim_f"] = {"hits": hits, "variants_calls": n_tc, "variants_result": n_vr, "adopted": n_ad, "cells_with_selection": n_cells, "retained": [ret, tot_sel]}


# ================================================================ hypothesis ledger, Holm, timing
LEDGER = [
    # block, file, lines (guess lines), written, held, missed, other, note
    ("E08", "TESTS.md", "103-105", 3, 2, 1, 0, "H3 rejected; H4, H5 supported"),
    ("E09", "TESTS.md", "130-131", 2, 0, 2, 0, "H6, H7 rejected"),
    ("E10", "TESTS.md", "154-157", 4, 2, 2, 0, "H10 supported; H11 'nominally supported' (rests on 2 improvements, counted held as written)"),
    ("E11", "TESTS.md", "254-257", 4, 4, 0, 0, "H12-H15 true"),
    ("E12", "TESTS.md", "345-350", 6, 4, 2, 0, "H19, H21 false; instrument later shown flawed"),
    ("E13", "TESTS.md", "480-485+", 6, 6, 0, 0, "H22-H27 true; author: none significant at cell level"),
    ("mp3", "TESTS.md", "574-577", 4, 2, 2, 0, "G-a..G-d"),
    ("GR1", "TESTS.md", "638-644", 5, 3, 2, 0, "toy network"),
    ("GR2", "TESTS.md", "695-700", 6, 5, 1, 0, "toy network"),
    ("GR3", "TESTS.md", "743-747", 5, 3, 2, 0, "toy network"),
    ("GR4", "TESTS.md", "809-816", 5, 5, 0, 0, "toy network"),
    ("SP1", "TESTS.md", "883-891", 8, 7, 1, 0, "stem pilot"),
    ("SP2", "TESTS.md", "1062-1070", 8, 6, 2, 0, "stem vs flat"),
    ("SP3", "TESTS.md", "1175-1193", 12, 6, 6, 0, "price and sense"),
    ("T-J3", "TESTS.md", "1268-1274", 6, 0, 1, 5, "storage limit; 5 not judged"),
    ("L1", "TESTS.md", "1482-1492", 8, 5, 3, 0, "heredity"),
    ("OpenAI blitz 1", "openai-cells-blitz/PREREGISTRATION.md", "H-B1..B4", 4, 1, 1, 2, "B2 indistinguishable, B3 sign check only"),
    ("OpenAI E18/E19", "openai-cells-blitz/PREREG-2,3,4.md", "17 H- lines", 17, 8, 9, 0, "tally in COST-EFFECTIVENESS.md; 5 'held' rest on the reported-selection counter later shown not to retain winners"),
    ("No-language", "no-language-colony/PREREG-5.md", "H-NL-A..P", 16, 4, 7, 5, "2 mixed (H, K) + F, I, P not evaluable counted in other"),
]
LEDGER_COLONY_LAWS = {"E11", "E12", "E13", "mp3", "SP1", "SP2", "SP3", "L1"}


def check_ledger():
    print("\n" + "=" * 100 + "\nPART 3: how many hypotheses were written down, how many held")
    T = read_text(LAWS / "TESTS.md").splitlines()
    pats = {"E08": (r"^- H[345]:", 3), "E09": (r"^- H[67]:", 2), "E10": (r"^- H(8|9|10|11):", 4), "E11": (r"^- H1[2345]:", 4),
            "E12": (r"^- H(16|17|18|19|20|21) ", 6), "E13": (r"^- H2[2-7] ", 6), "mp3": (r"^- G-[a-d] ", 4), "GR1": (r"^- GR-[a-e]:", 5),
            "GR2": (r"^- GR2-[a-f]:", 6), "GR3": (r"^- GR3-[a-e]:", 5), "GR4": (r"^- GR4-[a-e]\.", 5), "SP1": (r"^- SP-[a-h]\.", 8),
            "SP2": (r"^- S2-[a-h] ", 8), "SP3": (r"^- S3-[a-l] ", 12), "T-J3": (r"^- TJ-[a-f]\.", 6), "L1": (r"^- L1-[a-h]\.", 8)}
    # guess lines are the first occurrence of each ID pattern (before results restate them)
    for blk, (pat, want) in pats.items():
        lines = [i + 1 for i, l in enumerate(T) if re.match(pat, l)]
        first = []
        seen = set()
        for i in lines:
            key = re.match(pat, T[i - 1]).group(0)
            if key not in seen:
                seen.add(key)
                first.append(i)
        if len(first) != want:
            fail(f"{blk}: expected {want} guess lines, found {len(first)} ({first})")
    print("  guess lines located in TESTS.md for all 16 laws-record blocks (counts verified by regex, first occurrence of each ID).")
    W = H = M = O = 0
    print(f"  {'block':16} {'written':>7} {'held':>5} {'missed':>6} {'other':>5}   source / note")
    for blk, f, ln, w, h, m, o, note in LEDGER:
        if h + m + o != w:
            fail(f"ledger row {blk} does not add up")
        W += w; H += h; M += m; O += o
        print(f"  {blk:16} {w:7d} {h:5d} {m:6d} {o:5d}   {f} :: {ln}; {note}")
    print(f"  {'TOTAL':16} {W:7d} {H:5d} {M:6d} {O:5d}")
    laws = [r for r in LEDGER if r[0] in LEDGER_COLONY_LAWS]
    cw = sum(r[3] for r in laws); ch = sum(r[4] for r in laws); cm = sum(r[5] for r in laws)
    print(f"  agent-colony blocks that bear on claims a-e (E11, E12, E13, mp3, SP1, SP2, SP3, L1): written {cw}, held {ch}, missed {cm}")
    sp3_only = [r for r in LEDGER if r[0] == "SP3"][0]
    # post-hoc analyses
    post = []
    inz = False
    for i, l in enumerate(T):
        if re.search(r"NOT preregistered|not preregistered|DIAGNOSTIC|Diagnostic, NOT|Diagnostic \(NOT", l):
            post.append(i + 1)
    items = 0
    for s in post:
        j = s
        while j < len(T) and (j == s or not (T[j].startswith("#") or any(re.search(r"NOT preregistered|not preregistered|DIAGNOSTIC|Diagnostic", T[j]) for _ in [0]))):
            if re.match(r"^\s*(- |\d+\. |\|.*\|)", T[j]) and not T[j].startswith("|---") and not re.match(r"^\|\s*(kit|arm|run|guess)", T[j], re.I):
                items += 1
            j += 1
    print(f"  Outcomes analysed that were NOT written down: {len(post)} sections labelled 'not preregistered' / DIAGNOSTIC in TESTS.md (lines {post}); "
          f"about {items} bullet, numbered or table lines under them (rough count of separate post-hoc results)")
    print("  Also unregistered: sp3.py prints 6 pairwise arm contrasts x (O1, 4 per-part means, median of part differences, cell permutation p), "
          "O2 (4 parts x 4 arms), cost (5 measures x 4 arms) and behaviour lines B1-B7; only c-a, b-a and d-c on O1 were guessed (S3-i, S3-e, S3-l).")
    print("  Chain: GR2 'written after GR1', GR3 after GR2, GR4 after GR3, SP2 after SP1, SP3 after SP2, L1 after SP3: later guesses were set after "
          "seeing earlier results, so they are conditional on them (forking paths), not independent registrations.")
    OUT["ledger"] = {"written": W, "held": H, "missed": M, "other": O, "colony_laws": [cw, ch, cm], "post_sections": post, "post_items": items}
    return W, H, M, O


def timing():
    print("\n" + "=" * 100 + "\nPART 3b: were the guess files committed before the results they govern?")
    def git(repo, *a):
        r = subprocess.run(["git", "-C", str(repo)] + list(a), capture_output=True, text=True)
        if r.returncode != 0:
            return "ERR " + r.stderr.strip()
        return r.stdout.strip()
    rows = []
    for repo, name in ((WEFT, "weft"), (LOOM, "weft-loom")):
        if not (repo / ".git").exists():
            print(f"  {repo} is not a git checkout; skipped")
    print("  (read-only git log; weft-loom branch:", git(LOOM, "branch", "--show-current"), ")")
    # laws record, original repo (weft) per-file histories
    def log_weft(path):
        out = git(WEFT, "log", "--all", "--format=%h|%ad|%an|%s", "--date=iso", "--", path)
        return [x.split("|", 3) for x in out.splitlines() if x]
    base = "docs/program/experiments/razi-cells-laws-2026-11/"
    for f in ("TESTS.md", "code/cells/sp3.py", "results/sp3-out.txt", "code/cells/lineage_report.py", "results/l1-out.txt", "code/cells/sp2.py", "results/sp2-out.txt"):
        L = log_weft(base + f)
        print(f"  weft  {f}: " + " ; ".join(f"{a} {b[:19]}" for a, b, c, d in L))
    print("  -> TESTS.md (guesses AND results), the report scripts and the results/ outputs all arrive in squash commit 00ef7a8 (PR #107, 2026-11-10 06:42:42 -0600). "
          "Git cannot show any guess preceding its result for the laws record. Later commits touch TESTS.md only to append T-J3 text (checked below).")
    import difflib
    blob = git(WEFT, "show", "00ef7a8:" + base + "TESTS.md").splitlines()
    cur = read_text(LAWS / "TESTS.md").splitlines()
    ops = difflib.SequenceMatcher(None, blob, cur, autojunk=False).get_opcodes()
    nonins = [o for o in ops if o[0] not in ("equal", "insert")]
    ins = [(o[3] + 1, o[4]) for o in ops if o[0] == "insert"]
    print(f"  TESTS.md now vs the blob in commit 00ef7a8: non-insert differences {len(nonins)}; inserted line ranges {ins} "
          f"(the appended T-J3 R2 section). So no guess or result line was edited after the 2026-11-10 squash commit.")
    OUT["tests_md_edits"] = {"non_insert": len(nonins), "inserted": ins}
    # does the squashed commit message say so?
    msg = git(WEFT, "show", "-s", "--format=%B", "00ef7a8")
    print("  commit message mentions 'L1 full run finished after the record was cut':", "finished after the record was cut" in msg)
    # blitz and NL in weft-loom
    def log_loom(path):
        out = git(LOOM, "log", "--format=%h|%ad|%an|%s", "--date=iso", "--", path)
        return [x.split("|", 3) for x in out.splitlines() if x]
    b = "experiments/openai-cells-blitz-2026-11-12/"
    for f in ("PREREGISTRATION.md", "RESULTS.md", "PREREG-2.md", "PREREG-3.md", "PREREG-4.md", "RESULTS-E18.md", "harness.py"):
        L = log_loom(b + f)
        print(f"  loom  blitz/{f}: " + " ; ".join(f"{a} {t[:19]}" for a, t, c, d in L))
    for f in ("PREREG-5.md", "RESULTS-NL.md", "RESULTS-NL-STAGE2.md"):
        L = log_loom("experiments/no-language-colony-2026-11-12/" + f)
        print(f"  loom  no-language/{f}: " + " ; ".join(f"{a} {t[:19]}" for a, t, c, d in L))
    # which files each first commit contains
    first = {"3f1a3bc": ["PREREGISTRATION.md", "RESULTS.md"], "0edbd04": ["PREREG-2.md", "PREREG-3.md", "PREREG-4.md", "RESULTS-E18.md"]}
    for c, fs in first.items():
        tree = git(LOOM, "show", "--name-only", "--format=", c, "--", b)
        print(f"  commit {c}: contains {[f for f in fs if b + f in tree]} (and {sum(1 for l in tree.splitlines() if '/logs/' in l or '/cells/' in l)} log/cell files)")
    # raw log data windows
    print("  raw data windows from `t` fields in the committed logs (UTC-6 local), versus the 2026-11-10 06:42:42 commit:")
    def window(runs):
        ts = []
        for r in runs:
            d = ARCH / r
            if not d.exists():
                continue
            for p in list(d.glob("**/log.jsonl")) + list(d.glob("lineage.jsonl")):
                for x in jl(p):
                    if isinstance(x.get("t"), (int, float)):
                        ts.append(x["t"])
        return (min(ts), max(ts)) if ts else None
    import datetime as dt
    tz = dt.timezone(dt.timedelta(hours=-6))
    blocks = {
        "E11": [f"e11c{i}" for i in "1234"] + [f"e11n{i}" for i in "1234"],
        "E12": [f"e12{k}{i}" for k in ("c", "ch", "n", "nh") for i in "1234"],
        "E13": [f"e13{k}{i}" for k in ("c", "ch", "n", "nh") for i in "1234"],
        "SP1": ["fl1", "sp1", "fl2", "sp2"],
        "SP2": [f"s2{k}{i}" for i in "1234" for k in "fsm"],
        "SP3": [f"s3{k}{i}" for i in "1234" for k in "abcd"],
        "L1": [f"l1{k}{i}" for i in "123" for k in "hb"],
    }
    W = {}
    for k, runs in blocks.items():
        w = window(runs)
        W[k] = w
        if w:
            print(f"    {k:4} first t {dt.datetime.fromtimestamp(w[0], tz):%Y-%m-%d %H:%M:%S}  last t {dt.datetime.fromtimestamp(w[1], tz):%Y-%m-%d %H:%M:%S}")
        else:
            print(f"    {k:4} no timestamps")
    def win_files(files):
        ts = []
        for f in files:
            for l in read_text(f).splitlines():
                try:
                    d = json.loads(l)
                except Exception:
                    continue
                if isinstance(d, dict) and isinstance(d.get("t"), (int, float)):
                    ts.append(d["t"])
        return (min(ts), max(ts)) if ts else None
    for name, files, commit in (
            ("blitz wave 1 (astra-1..4, sol, luna logs)", sorted((BLITZ / "logs").glob("astra-[1-4].jsonl")) + sorted((BLITZ / "logs").glob("sol-*.jsonl"))[:0], "PREREGISTRATION.md + RESULTS.md committed 2026-11-12 10:41:32"),
            ("blitz E18/E19 (all logs)", [p for p in sorted((BLITZ / "logs").glob("*.jsonl")) if p.name != "usage.jsonl"], "PREREG-2,3,4 + RESULTS-E18 committed 2026-11-12 12:25:26"),
            ("no-language (all logs)", sorted((NL / "logs").glob("*.jsonl")), "PREREG-5 first committed 2026-11-12 15:43:37 (with Stage 1 results)")):
        w = win_files(files)
        W[name] = w
        print(f"    {name}: first t {dt.datetime.fromtimestamp(w[0], tz):%Y-%m-%d %H:%M:%S}  last t {dt.datetime.fromtimestamp(w[1], tz):%Y-%m-%d %H:%M:%S}   | {commit}")
    OUT["timing_windows"] = {k: (list(v) if v else None) for k, v in W.items()}
    # guess text unchanged between pre-result snapshot and final TESTS.md
    print("  guess text: archive snapshots TESTS_pre_*.md (copies of TESTS.md taken before each result was appended) vs final TESTS.md:")
    Tfinal = read_text(LAWS / "TESTS.md")
    final_lines = {l.strip() for l in Tfinal.splitlines()}
    snaps = {"SP1": ("TESTS_pre_SP1_result.md", r"^- SP-[a-h]\."), "SP2": ("TESTS_pre_SP2_result.md", r"^- S2-[a-h] "), "SP3": ("TESTS_pre_sp3result.md", r"^- S3-[a-l] "),
             "L1": ("TESTS_pre_l1result.md", r"^- L1-[a-h]\."), "GR3": ("TESTS_pre_GR3_results.md", r"^- GR3-[a-e]:"), "GR4": ("TESTS_pre_GR4_result.md", r"^- GR4-[a-e]\."),
             "E11": ("TESTS_pre_e11_results.md", r"^- H1[2-5]:"), "E12": ("TESTS_pre_e12_results.md", r"^- H(16|17|18|19|20|21) "), "E13": ("TESTS_pre_e13_results.md", r"^- H2[2-7] "),
             "mp3": ("TESTS_pre_mp3_results.md", r"^- G-[a-d] ")}
    same = {}
    for blk, (fn, pat) in snaps.items():
        p = ARCH / "archive" / fn
        if not p.exists():
            print(f"    {blk}: snapshot {fn} missing")
            continue
        S = read_text(p).splitlines()
        gl = []
        seen = set()
        for l in S:
            m = re.match(pat, l)
            if m and m.group(0) not in seen:
                seen.add(m.group(0))
                gl.append(l.strip())
        has_result = any(re.search(rf"{blk} result|{blk} Result", l, re.I) for l in S)
        ident = sum(1 for l in gl if l in final_lines)
        same[blk] = (ident, len(gl))
        print(f"    {blk:4} snapshot {fn}: {len(gl)} guess lines, {ident} identical in final TESTS.md; snapshot already contains a '{blk} result' heading: {has_result}")
    OUT["guess_unchanged"] = same
    print("  The snapshots prove the guess WORDING did not change after results were added (where identical), and that the snapshot lacked the result section, "
          "but the snapshots arrive in the 2026-11-13 archive commit, so wall-clock order rests on the author's own timestamps and on the `t` fields above, not on git.")
    return W


# ================================================================ Holm
def holm_part(res):
    print("\n" + "=" * 100 + "\nPART 3c: Holm correction (alpha 0.05) over the primary run-level tests behind claims a to e")
    pv = res
    adj = holm(pv)
    m = len(pv)
    print(f"  family size m = {m}. Raw p are exact permutation / Fisher p at the run level (the cell-level Fisher for deaths is shown for comparison in claim b).")
    print(f"  {'test':58} {'raw p':>10} {'Holm p':>10}  survives 0.05")
    for k, p in sorted(pv.items(), key=lambda kv: kv[1]):
        print(f"  {k:58} {p:10.4g} {adj[k]:10.4g}  {'YES' if adj[k] < 0.05 else 'no'}")
    N = OUT["ledger"]["written"]
    thr = 0.05 / N
    print(f"  Wider family: all {N} hypotheses written down across the records. Bonferroni/Holm first-step threshold 0.05/{N} = {thr:.2e}. "
          f"Tests below that: {[k for k, p in pv.items() if p < thr] or 'none'}")
    print("  Note: most written guesses are threshold rules on point estimates and have no p value, so Holm cannot be applied to them; "
          "the 4 vs 4 and 3 vs 3 designs have a smallest attainable two-sided exact p of 0.0286 and 0.10.")
    OUT["holm"] = {"raw": pv, "adj": adj, "m": m, "wide_threshold": thr}


def main():
    quick = "--quick" in sys.argv
    if WEFT is None:
        raise SystemExit("colony_stats: PART 3b reads the git history of the weft software checkout; give it with --weft PATH or the WEFT_CHECKOUT environment variable")
    sp3 = sp3_cells()
    rel = rel_table(LAWS / "results/sp3-ref.json")
    ra = claim_a(sp3)
    rb = claim_b(sp3)
    rc = claim_c(sp3, rel)
    rd = claim_d()
    re_ = claim_e()
    claim_f()
    check_ledger()
    timing()
    pv = {
        "a  step-0 light, shown vs hidden (8 vs 8 runs)": OUT["claim_a"]["sp3"]["runlevel_p_8v8"],
        "a  step-0 light, arm a vs arm b (4 vs 4 runs, S3-c)": OUT["claim_a"]["sp3"]["runlevel_p_ab"],
        "b  energy, arm b vs arm a (4 vs 4 runs, S3-e)": OUT["claim_b"]["res"]["b/a (sense hidden)"]["p"],
        "b  energy, hidden vs shown (8 vs 8 runs)": OUT["claim_b"]["res"]["hidden_vs_shown"]["p"],
        "b  runs with a death, hidden vs shown (Fisher 8 vs 8)": OUT["claim_b"]["res"]["deaths"]["runs_p"],
        "c  sense c vs a, O1 all kits (S3-i, 4 vs 4 runs)": OUT["claim_c"]["run_perm"]["p"],
        "c  sense c vs a, O1 without fibmod (4 vs 4 runs)": OUT["claim_c"]["run_perm_nofib"]["p"],
        "c  sense main effect, O1 (8 vs 8 runs)": OUT["claim_c"]["main_effect"]["p"],
        "c  sense main effect, O1 without fibmod (8 vs 8)": OUT["claim_c"]["main_effect_nofib"]["p"],
        "c' hidden vs shown on reach b vs a (4 vs 4 runs)": OUT["claim_c"]["b_minus_a"]["p"],
        "d  stem vs flat reach SP2 (4 vs 4 runs)": OUT["claim_d"]["sp2_reach"]["p"],
        "d  stem vs flat tokens SP2 (4 vs 4 runs)": OUT["claim_d"]["sp2_tokens"]["p"],
        "e  heredity vs blank energy L1 (3 vs 3 runs)": OUT["claim_e"]["p"],
        "e  heredity vs blank reach L1 (3 vs 3 runs)": OUT["claim_e"]["O1"][1],
    }
    holm_part(pv)
    check_integrity()
    OUT["rel_path"] = str(LAWS / "results/sp3-ref.json")
    (HERE / "colony_results.json").write_text(json.dumps(OUT, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    print("\nwrote", HERE / "colony_results.json")


if __name__ == "__main__":
    main()
