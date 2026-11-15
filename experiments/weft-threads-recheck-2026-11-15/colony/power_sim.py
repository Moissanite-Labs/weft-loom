#!/usr/bin/env python3
"""power_sim.py: power for the proposed replication, from the empirical run-level distribution in the SP3 raw data.

Reads results of the same raw files as colony_stats.py (SP3 ledgers, logs, sp3-ref.json). Writes power_results.json here.

  /path/to/python -I power_sim.py

Part 5: sense effect on reach (O1, one number per run), per model family, 80% and 90% power, alpha 0.05 two-sided.
Part 6: scrambled-price control: which comparison separates "reads the prices" from "follows model names", and runs needed.
All simulation: resampling of observed run-level residuals (no parametric noise model), SEED fixed.
"""
import itertools
import json
import math
import os
import statistics
import sys
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import colony_stats as cs  # noqa: E402  (module-level code only defines functions; main() is not run on import)

SEED = 20261116
SIMS = 6000
ALPHA = 0.05
OUT = {}
KITS = cs.KITS


def fail(m):
    raise SystemExit("power_sim FAILED: " + m)


def welch_power(rng, resid, n, delta, sims=SIMS):
    x = rng.choice(resid, (sims, n))
    y = rng.choice(resid, (sims, n)) + delta
    mx, my = x.mean(1), y.mean(1)
    vx, vy = x.var(1, ddof=1), y.var(1, ddof=1)
    se2 = vx / n + vy / n
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (my - mx) / np.sqrt(se2)
        df = se2 ** 2 / ((vx / n) ** 2 / (n - 1) + (vy / n) ** 2 / (n - 1))
        p = 2 * stats.t.sf(np.abs(t), df)
    p = np.where(np.isfinite(p), p, np.where(my != mx, 0.0, 1.0))
    return float((p < ALPHA).mean())


_MASKS = {}


def perm_power(rng, resid, n, delta, sims=SIMS):
    """Power of the exact two-sided permutation test on the difference of means (n <= 7)."""
    if n not in _MASKS:
        idx = list(itertools.combinations(range(2 * n), n))
        M = np.zeros((len(idx), 2 * n))
        for i, c in enumerate(idx):
            M[i, list(c)] = 1
        _MASKS[n] = M
    M = _MASKS[n]
    x = rng.choice(resid, (sims, n))
    y = rng.choice(resid, (sims, n)) + delta
    Z = np.concatenate([x, y], axis=1)
    tot = Z.sum(1, keepdims=True)
    s1 = Z @ M.T
    stat = s1 / n - (tot - s1) / n
    obs = Z[:, n:].mean(1) - Z[:, :n].mean(1)
    # observed split is (y group = second half); its statistic is mean(y) - mean(x); the mask enumerates first-group sums
    # use |stat| >= |obs| with the sign convention folded by the absolute value
    p = (np.abs(stat) >= np.abs(obs)[:, None] - 1e-12).mean(1)
    return float((p < ALPHA).mean()), float(M.shape[0])


def normal_n(sigma, delta, power):
    za, zb = stats.norm.ppf(1 - ALPHA / 2), stats.norm.ppf(power)
    return math.ceil(2 * (za + zb) ** 2 * sigma ** 2 / delta ** 2)


def t_n(sigma, delta, power):
    for n in range(2, 5000):
        df = 2 * n - 2
        tc = stats.t.ppf(1 - ALPHA / 2, df)
        nc = delta / (sigma * math.sqrt(2 / n))
        pw = stats.nct.sf(tc, df, nc) + stats.nct.cdf(-tc, df, nc)
        if pw >= power:
            return n
    return None


def first_n(rng, resid, delta, target, grid):
    for n in grid:
        if welch_power(rng, resid, n, delta) >= target:
            return n
    return None


def main():
    rng = np.random.default_rng(SEED)
    sp3 = cs.sp3_cells()
    rel = cs.rel_table(cs.LAWS / "results/sp3-ref.json")
    print("=" * 100 + "\nPART 5: power for the sense effect on reach (O1 per run)")
    cs.src(cs.LAWS / "results/sp3-ref.json", "rel -> O1 per run = median over kits; residuals = O1 minus arm mean, arms a and c (price shown, as in the proposed design)")
    O1 = {a: np.array([cs.o1(rel, r) for r in cs.SP3[a]]) for a in "abcd"}
    O1nf = {a: np.array([cs.o1(rel, r, ("compress", "csvsum", "maze")) for r in cs.SP3[a]]) for a in "abcd"}
    scen = {}
    for name, D in (("all four kits (as run)", O1), ("without fibmod (the proposal drops or replaces it)", O1nf)):
        resid = np.concatenate([D["a"] - D["a"].mean(), D["c"] - D["c"].mean()])
        resid = resid * math.sqrt(len(resid) / (len(resid) - 2))  # centred residuals understate the variance by (n-k)/n; rescale to the unbiased pooled SD
        sig = math.sqrt((D["a"].var(ddof=1) + D["c"].var(ddof=1)) / 2)
        resid4 = np.concatenate([D[a] - D[a].mean() for a in "abcd"]) * math.sqrt(16 / 12)
        sig4 = math.sqrt(np.mean([D[a].var(ddof=1) for a in "abcd"]))
        obs = float(D["c"].mean() - D["a"].mean())
        scen[name] = dict(resid=resid, sig=sig, resid4=resid4, sig4=sig4, obs=obs)
        print(f"  {name}: run SD a {D['a'].std(ddof=1):.3f}, c {D['c'].std(ddof=1):.3f}, pooled {sig:.3f} (all four arms {sig4:.3f}); observed c - a = {obs:+.4f}")
    SMALL = 0.10
    print(f"  Assumption for 'smallest effect the team would care about': +{SMALL:.2f} on O1. This is the team's own 'level' band and the S3-i threshold in TESTS.md "
          f"(arms closer than 0.10 are called level), about {100*SMALL/np.mean(O1['a']):.0f}% of the control arm's O1 {np.mean(O1['a']):.2f}.")
    grid = list(range(2, 31)) + list(range(32, 81, 2)) + list(range(85, 301, 5))
    res = {}
    for name, S in scen.items():
        print(f"\n  --- design ground: {name}")
        obs = S["obs"]
        deltas = {"observed": obs, "half observed": obs / 2, f"smallest (assumed) {SMALL:.2f}": SMALL}
        res[name] = {}
        print(f"  {'true effect':26} {'delta':>7} {'d=delta/sd':>10} | n per arm for 80% power: normal(z)  normal(t)  simulation | 90%: normal(z)  normal(t)  simulation")
        for lab, dl in deltas.items():
            if dl <= 0:
                print(f"  {lab:26} {dl:7.3f}  not positive: no n gives power; the effect on these kits is zero or negative in the data")
                res[name][lab] = {"delta": dl, "note": "not positive"}
                continue
            row = {"delta": dl}
            line = f"  {lab:26} {dl:7.3f} {dl/S['sig']:10.2f} |"
            for tgt in (0.8, 0.9):
                nz, nt = normal_n(S["sig"], dl, tgt), t_n(S["sig"], dl, tgt)
                ns = first_n(rng, S["resid"], dl, tgt, grid)
                row[str(tgt)] = {"z": nz, "t": nt, "sim": ns}
                line += f" {nz:11d} {nt if nt is not None else -1:10d} {ns if ns is not None else -1:11d} |"
            print(line)
            res[name][lab] = row
        # joint requirement: both families must show the gain
        print("  Both families must pass (the proposed pass mark). Each family tested separately at alpha 0.05; joint power = product of per-family powers.")
        for lab, dl in deltas.items():
            if dl <= 0:
                continue
            row = res[name][lab]
            line = f"    {lab:26}"
            for tgt, per in ((0.8, math.sqrt(0.8)), (0.9, math.sqrt(0.9))):
                ns = first_n(rng, S["resid"], dl, per, grid)
                row[f"joint_{tgt}"] = ns
                line += f" joint {int(tgt*100)}% needs per-family power {per:.3f}: n per arm per family {ns if ns is not None else '>300'};"
            print(line)
        # variance assumption for second family
        print("  If the second family's run-to-run SD is 1.5 times the first (unknown; no data exist for it):")
        r15 = S["resid"] * 1.5
        for lab, dl in deltas.items():
            if dl <= 0:
                continue
            n80 = first_n(rng, r15, dl, 0.8, grid)
            n90 = first_n(rng, r15, dl, 0.9, grid)
            res[name][lab]["sd1.5"] = {"0.8": n80, "0.9": n90}
            print(f"    {lab:26} n per arm: 80% {n80}, 90% {n90}")
    # what 3 to 4 runs can detect
    print("\n  What the current 3 to 4 runs per arm can detect (80% power, alpha 0.05 two-sided, same resampled variance):")
    det = {}
    for name, S in scen.items():
        det[name] = {}
        dgrid = np.arange(0.025, 3.0, 0.025)
        for n in (3, 4):
            wd = next((float(d) for d in dgrid if welch_power(rng, S["resid"], n, d) >= 0.8), None)
            pp = [(float(d), perm_power(rng, S["resid"], n, d)[0]) for d in (0.25, 0.5, 0.75, 1.0)]
            pm = next((float(d) for d in dgrid if perm_power(rng, S["resid"], n, d)[0] >= 0.8), None)
            det[name][n] = {"welch_mde80": wd, "perm_mde80": pm, "perm_power": pp}
            print(f"    {name}: n = {n} per arm: smallest effect with 80% power, Welch t {wd:.3f} (= {wd/S['sig']:.1f} SD)" +
                  (f"; exact permutation test {pm:.3f}" if pm else "; exact permutation test: never reaches 80% in range (smallest p possible is "
                   f"{2/math.comb(2*n, n):.3f})"))
            print(f"       exact-permutation power at effects 0.25/0.5/0.75/1.0: " + ", ".join(f"{d}: {p:.2f}" for d, p in pp))
    res["detectable"] = det
    # how the p-value floor looks
    for n in (3, 4, 5, 6):
        print(f"  smallest two-sided exact permutation p with {n} vs {n} runs: {2/math.comb(2*n, n):.4f}")
    OUT["part5"] = {k: v for k, v in res.items()}
    OUT["part5_assumption_small"] = SMALL

    # ---------------------------------------------------------------- part 6
    print("\n" + "=" * 100 + "\nPART 6: scrambled-price control (reads the prices vs follows model names)")
    sp3c = sp3
    shown_runs = []
    for a in "ac":
        for r in cs.SP3[a]:
            shown_runs.append(sum(c["light0"] for c in sp3c[a][r]))
    # SP2 arm f runs
    f_runs = []
    for r in ["s2f1", "s2f2", "s2f3", "s2f4"]:
        k = 0
        for kit in KITS:
            R = cs.jl(cs.ARCH / r / kit / "log.jsonl")
            models = [x["model"] for x in R if isinstance(x.get("usage"), dict)]
            fn = next((x["next"] for x in R if "act" in x and "step" in x and x.get("next")), None)
            k += int(models[0] == "mid" and fn is not None and fn[0] == "light")
        f_runs.append(k)
    shown_runs += f_runs
    m = 4
    xs = np.array(shown_runs, float)
    p_hat = xs.mean() / m
    msb = m * np.var(xs / m, ddof=1)
    # ANOVA ICC for equal clusters: (MSB - MSW) / (MSB + (m-1) MSW); MSW = within-run variance of cell indicators
    msw = (xs * (m - xs) / m).sum() / (len(xs) * (m - 1))
    msb2 = m * np.sum((xs / m - p_hat) ** 2) / (len(xs) - 1)
    icc = (msb2 - msw) / (msb2 + (m - 1) * msw)
    print(f"  shown-list run counts of cells (of 4) moving to light at step 0 (SP3 a, SP3 c, SP2 f; 12 runs): {shown_runs}; mean per cell {p_hat:.3f}")
    print(f"  intraclass correlation by run (ANOVA estimator): {icc:+.3f} (negative or near zero means the misses are not clustered by run; they cluster by KIT: "
          f"all 6 SP3 shown-arm misses are fibmod cells)")
    OUT["part6_icc"] = float(icc)
    print("""
  COMPARISON THAT SEPARATES THE TWO READINGS
    Arms (4 kits per run, every cell born on mid, true prices charged in all arms):
      T  true list shown (light cheapest, as run)
      S  scrambled list: the same three numbers shown against the wrong names. Swap the light and heavy rows so the model that LOOKS cheapest on the
         list is heavy and light looks dearest; leave mid unchanged. Charges stay true.
      H  list hidden
    Outcome per cell (first `next` model after step 0, as sp3.py B1): L = chose light, D = chose the model that looks cheapest on the displayed list
         (light in T, heavy in S).
    Primary statistic: risk difference  P(L | T) - P(L | S), tested at the run level (4 cells per run; exact permutation of per-run proportions, or the
         difference of run means with a bootstrap over runs).
         Reads the prices   -> P(L | S) falls toward the hidden-arm rate (0 of 32 in SP3) and P(D | S) rises above P(D | H).
         Follows the names  -> P(L | S) stays near P(L | T) (0.83) and P(D | S) stays near P(D | H) = 0.
    Control checks: P(L | S) against P(L | H) (is anything left that the names alone do?), and P(heavy | S) alone, noting a cell that reads the numbers
         but doubts a list that calls heavy cheapest can also stay on mid: the L contrast is the one that does not depend on that.""")
    # power
    def bb_runs(rng, p, rho, n, sims):
        """run counts out of 4 cells with intra-run correlation rho (beta-binomial)."""
        if rho <= 1e-9 or p <= 0 or p >= 1:
            return rng.binomial(m, p, (sims, n)).astype(float) / m
        a = p * (1 - rho) / rho
        b = (1 - p) * (1 - rho) / rho
        pr = rng.beta(a, b, (sims, n))
        return rng.binomial(m, pr).astype(float) / m

    def power_props(pT, pS, rho, n, sims=4000):
        x = bb_runs(rng, pT, rho, n, sims)
        y = bb_runs(rng, pS, rho, n, sims)
        # exact permutation for n <= 6 else Welch
        if n <= 6:
            if n not in _MASKS:
                idx = list(itertools.combinations(range(2 * n), n))
                M = np.zeros((len(idx), 2 * n))
                for i, c in enumerate(idx):
                    M[i, list(c)] = 1
                _MASKS[n] = M
            M = _MASKS[n]
            Z = np.concatenate([x, y], axis=1)
            tot = Z.sum(1, keepdims=True)
            s1 = Z @ M.T
            stat = s1 / n - (tot - s1) / n
            obs = Z[:, :n].mean(1) - Z[:, n:].mean(1)
            p = (np.abs(stat) >= np.abs(obs)[:, None] - 1e-12).mean(1)
            return float((p < ALPHA).mean())
        mx, my = x.mean(1), y.mean(1)
        vx, vy = x.var(1, ddof=1), y.var(1, ddof=1)
        se2 = vx / n + vy / n
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (mx - my) / np.sqrt(se2)
            df = se2 ** 2 / (np.where(vx > 0, (vx / n) ** 2, 0) / (n - 1) + np.where(vy > 0, (vy / n) ** 2, 0) / (n - 1))
            p = 2 * stats.t.sf(np.abs(t), df)
        p = np.where(np.isfinite(p), p, np.where(mx != my, 0.0, 1.0))
        return float((p < ALPHA).mean())

    pT = float(p_hat)
    print(f"\n  Runs needed per arm (4 cells per run; per-run proportions; exact permutation for n <= 6 runs else Welch; alpha 0.05 two-sided).")
    print(f"  True P(L | T) = {pT:.2f} (pooled shown-list rate, SP2 f + SP3 a + SP3 c). Sweep P(L | S) and run-level correlation rho.")
    tab = {}
    print(f"  {'P(L|S)':>7} {'rho':>5} | runs per arm for 80% / 90% power to see S below T")
    for pS in (0.0, 0.05, 0.2, 0.4):
        for rho in (0.0, 0.2):
            found = []
            for tgt in (0.8, 0.9):
                nn = next((n for n in range(2, 41) if power_props(pT, pS, rho, n) >= tgt), None)
                found.append(nn)
            tab[f"{pS}_{rho}"] = found
            print(f"  {pS:7.2f} {rho:5.1f} | {found[0]} / {found[1]}")
    print("  (true P(L|S) = 0 is the clean 'reads the prices' case; 0.4 is a half-and-half cell population)")
    print("  Price effect itself (T versus H): observed 26/32 shown (and 40/48 pooled) vs 0/32 hidden.")
    for rho in (0.0, 0.2):
        found = []
        for tgt in (0.8, 0.9):
            nn = next((n for n in range(2, 41) if power_props(pT, 0.0, rho, n) >= tgt), None)
            found.append(nn)
        tab[f"T_vs_H_{rho}"] = found
        print(f"    rho {rho}: runs per arm for 80% / 90%: {found[0]} / {found[1]} (with 4 runs per arm the exact test's floor is 0.0286, so 4 is the minimum at alpha 0.05)")
    # also if the true effect shrinks (winner's curse): pT = 0.6
    for pT2 in (0.6,):
        found = []
        for tgt in (0.8, 0.9):
            nn = next((n for n in range(2, 41) if power_props(pT2, 0.0, 0.2, n) >= tgt), None)
            found.append(nn)
        print(f"    if the true shown-list rate were only {pT2:.1f} (rho 0.2): runs per arm 80% / 90%: {found[0]} / {found[1]}")
        tab[f"T{pT2}_vs_H"] = found
    OUT["part6"] = tab
    (HERE / "power_results.json").write_text(json.dumps(OUT, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    print("\nwrote", HERE / "power_results.json")


if __name__ == "__main__":
    main()
