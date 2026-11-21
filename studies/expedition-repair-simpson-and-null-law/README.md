# Expedition Study: Repair-Signal Compute-Leakage Simpson's Paradox & Exact Null-Space / Schur-Complement Audits

- **Question.** (1) On `Moissanite-Labs/weft-loom` PR `#38`'s live 2,687-round repair-signal dataset (`Qwen3.8-27B-AD-Q4_K_M`, Tiers S & M), does contradictory sign-flipped feedback (`D`) genuinely outperform true-sign feedback (`C`), or is the raw `D > C` lead a compute-leakage Simpson's paradox? (2) On `main`'s committed `null_law.json`, `probe_count_tf.json`, and `budget-curve.json`, does null-space leakage obey a global scale-free power law, what governs `heedle`'s blind-adversary Schur complement, and what separates passing vs. failing Transformer `H4` seeds?
- **Status.** `analysis-verified` (independent R1–R5 verification audits `AUDIT-023` and `AUDIT-025`; pure Python 3 stdlib, zero external dependencies, bit-identical across all 4 isolated `-I` interpreter modes).
- **Preregistration.** Not preregistered (post-hoc exact algebraic & statistical audit of committed live upstream artifacts in `weft-loom` `main` and PR `#38` `f7377ee`).
- **Disclosure.** Scripts, exact algebraic certificates, and analysis were produced and independently audited with AI assistance as part of the Foundation-0 / Moissanite-Labs cross-repo verification sprint.

---

## 1. Repair-Signal Two-Channel Simpson's Paradox (`probe_s1_repair_signal_two_channel.py`)

### Prior-Art Credit (PR `#38` `f7377ee`)
PR `#38`'s own `README.md` (`f7377ee`) already flagged the qualitative `79.6s vs 3.0s` open-reasoning confound and the `113/116` next-round pass rate after format-breaking replies, while explicitly leaving fast-channel arm comparisons as *"untested ... a lead and nothing more."* This probe provides the exact rational paired binomial (`fractions.Fraction`) Simpson's reversal proof, the full wall-clock survival sweep across compute budgets, and the exact rational constraint-excess contraction analysis.

### Key Results (`Qwen3.8-27B-AD-Q4_K_M`, Tier S $n=100$, Tier M $n=100$; `2,687` live rounds)

| Regime / Metric (Tier S, $n=100$ paired instances) | Arm A (verdict) | Arm B (place) | Arm C (true sign) | Arm D (sign flipped) | Exact Paired Binomial Test (Pure `Fraction`) |
|---|---:|---:|---:|---:|---|
| **Fixed-compute $T \le 10\text{s}$** | `23` | `44` | **`47`** | `39` | **`C > D`: `11 vs 3`, $p = 0.0287$** |
| **Fixed-compute $T \in [15, 45]\text{s}$** (and pure-readable, zero escape) | `23` | `48` | **`56`** | `44` | **`C > D`: `15 vs 3`, $p = 0.00377$** (`C > B`: `14 vs 6`, $p = 0.0577$) |
| **Fixed-compute $T \le 60\text{s}$** | `25` | `48` | **`56`** | `46` | **`C > D`: `13 vs 3`, $p = 0.01064$** (crosses at `T = 90s`: `8 vs 10`) |
| **Round-2 direct solve** (before R3 escape payoff) | `1` | `16` | **`21`** | `14` | **`C > D`: `9 vs 2`, $p = 0.03271$** |
| **Round-2 `80s` CoT format-escape** (`--reasoning off` break) | `43` | `27` | **`13`** | **`33`** | **`D > C`: `20 vs 0`, $p = 9.54 \times 10^{-7}$** (**Tier M: `17 vs 1`, $p = 7.25 \times 10^{-5}$**; **Pooled S+M: `37 vs 1`, $p = 1.42 \times 10^{-10}$**) |
| **Total wall-clock compute spent** (100 instances) | `4,202s` | `2,769s` | **`1,825s`** | `3,168s` | **`D` spent `1.736x` more compute than `C`** |
| **Unbounded 4-round pass** ($T \in [120, 300]\text{s}$, raw count) | `65` | `75` | `69` | **`77`** | **`D > C`: `11 vs 3`, $p = 0.02869$ (complete sign reversal)** |

- **Data Provenance:** Exact reproduction of PR `#38` `recount.txt` (`S: A=65, B=75, C=69, D=77`; `M: A=2, B=8, C=7, D=12`; `100/100` identical R1 replies). The two PR `#38` JSONL files (`3.1 MB`, within `CONTRIBUTING.md`'s 5 MB raw-data rule) are committed under `data/weft_loom_pr38/` so this study runs standalone before PR `#38` merges.
- **Exact Rational $\ell_1$ Contraction Nuance (R1 $\to$ R2 readable):** Raw readable improvement counts favor `C` on both tiers (S: `44` vs `B=33, D=30, A=1`; M: `34` vs `B=27, D=22, A=1`, with `D` solving `0/70` pure-readable on M). Conditioned strictly on the `45` Tier-S instances where *both* `C` and `D` stayed readable at R2, $\ell_1$ improvement ties (`30/45` vs `30/45`, conditional `67.7%` vs `66.7%`, strict $\ell_1$ `3 vs 4`, $p = 0.773$), whereas on Tier M (`69` both-readable) `C` leads `29 vs 21` (strict $\ell_1$ `13 vs 6`, $p = 0.0835$). Thus Tier S's raw `44 vs 30` gap is itself driven by `C` remaining readable while `D` escapes into `80s` open reasoning.
- **Controls:** `5,000`-trial seeded within-instance permutation nulls, R1 identical-reply negative control (`0` discordant, $p = 1.0$), and `4/4` strict input/type guards.

---

## 2. Exact Null-Law Farkas Certificate, Generalized Schur Pencil & Transformer/CBC Audits (`probe_s3_weft_nullspace_schur_law.py`)

Reads committed repo-root artifacts directly (`experiments/gate-metric-calibration-2026-11-15/{null_law.json,results_tf.summary.json,probe_count_tf.json}` and `experiments/committed-behaviour-change-2026-11-15/budget-curve.json`):

1. **Exact Zero-Log BigInt Refutation of Scale-Free Null-Space Decay (`null_law.json`, 12 MLP hosts $\times$ 6 dyadic `n_keep = 16..512`):**
   - **Global 6-scale power law at $\pm 2\text{ SE}$: REFUTED in pure BigInt arithmetic** (`max_violation = 1.40115 > 1`, zero floats, zero logs; synthetic power-law control passes).
   - **4-ray Farkas tail window (`64..512`):** Refutes convex decelerating decay while keeping concave accelerating finite-rank decay feasible at $\pm 1.0\text{ SE}$ and $\pm 1.5\text{ SE}$ (both stay feasible at unpaired $\pm 2.0\text{ SE}$ due to between-host amplitude variance).
   - **Paired within-host cross-ratios $R_k^{(h)}$ (canceling host amplitude):** **`12/12` hosts strictly concave (`R < 1`)** at both `n_keep = 128` (`max = 0.9886`) and `n_keep = 256` (`max = 0.9636`), exact binomial **`p = 1/4096 = 2.44e-4`** each.
2. **Exact Zero-Float Generalized Pencil $(G_{\mathrm{held}} - \lambda G_{\mathrm{probe}})$ & `heedle` Schur Complement ($S_{\mathrm{shed}}$):**
   - Pure-`Fraction` Bunch–Kaufman inertia certifies exact non-commuting blind-adversary RMS hiding ratio `[45.896418, 45.896418]` with exact permutation gauge invariance and zero-blindspot control (`ratio < 1`).
   - Certifies the exact Schur Complement identity $S_{\mathrm{shed}} := K_{\mathrm{oo}} - K_{\mathrm{ok}} K_{\mathrm{kk}}^{-1} K_{\mathrm{ko}} \equiv J_{\mathrm{out}} \Pi_{\mathrm{shed}} J_{\mathrm{out}}^\top$ (`0` residual over $\mathbb{Q}$), exact power-trace duality $\operatorname{tr}(W_{\mathrm{shed}}^m) \equiv \operatorname{tr}(S_{\mathrm{shed}}^m)$ ($m = 1..4$), and zero-float spectral ceiling $\lambda_{\max}(S_{\mathrm{shed}}) \in [22.78609321, 22.78609321]$ (independently matched against live `heedle/core.py` `hidden_move` with `rel_err == 0.0`).
3. **Transformer `H4` Spatial-Leverage Separation (`probe_count_tf.json`) & CBC Budget Saturation (`budget-curve.json`):**
   - Failing Transformer seeds `{4, 5, 7}` have **`top5_pct_share_of_sq_change in [0.5635, 0.8797]`**, strictly separated (`100%`, exact permutation $p = 1/20 = 0.05$ for `n = 3 vs 3`) from passing seeds `{0, 1, 2}` in **`[0.3634, 0.4970]`**.
   - Across all 12 CBC benign grafts up to `600,000` rows, `1/12` crosses (`pair 1015` at row `40,719`) while all 11 non-crossing pairs saturate (`max gain 100k -> 600k = 6.75e-5`).

---

## 3. How to Rerun (4-Mode Isolated R4 Parity)

From the repository root (pure Python 3 stdlib, zero external dependencies):

```bash
for flags in "-I -B" "-I -O -B" "-I -B -W error" "-I -O -B -W error"; do
  python3 $flags studies/expedition-repair-simpson-and-null-law/probe_s1_repair_signal_two_channel.py
  python3 $flags studies/expedition-repair-simpson-and-null-law/probe_s3_weft_nullspace_schur_law.py
done
```

Expected deterministic artifact SHA-256 digests:
- `probe_s1_repair_signal_results.json`: `2afbfdbe31478267fbc7231c90b4c899f624b7873f6475d575594e8757e0b760`
- `probe_s3_weft_nullspace_results.json`: `c3fe222f5b233b8644d4ada5dd58971427d1158feeacab0b6fbf3381aaa59fa9`

---

## 4. Limits

- **PR `#38` scope:** Single quantized model (`Qwen3.8-27B-AD-Q4_K_M`) and `n = 100` instances per tier; wall-clock survival splits are post-hoc stratification of logged round timestamps rather than a fresh hardware-capped rerun (though `R2` direct solve and `R2` format-escape are strictly causal before `R3` payoff).
- **Transformer `H4` leverage:** `n = 3 vs 3` seeds yields the smallest achievable two-sample permutation $p$-value ($1/20 = 0.05$), so the `[0.36, 0.50]` vs `[0.56, 0.88]` threshold is a strong diagnostic hypothesis rather than a large-sample asymptotic proof.
- **Singular Gram matrices:** `probe_s3`'s Schur complement assumes nonsingular $G_{\mathrm{kk}}$; rank-deficient cases generalize via Moore–Penrose pseudoinverse / Haynsworth inertia.
