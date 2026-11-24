# E11 — Horizontal plasmid transfer (Breaking through)

Status: `[measured]` prereg-faithful reruns, 2026-11-14 (canonical record in **weft-loom**; ported from [weft#201](https://github.com/Moissanite-Labs/weft/pull/201)).  
Issue: [#149](https://github.com/Moissanite-Labs/weft/issues/149).  
Preregistration: `PREREG.md` (unchanged).  
Runner: `run_e11.py` (NumPy, CPU).  
Raw JSON: `results/e11_results.json`.

## Context

`[derived]` Prior Astra / weight-edit work ([#146](https://github.com/Moissanite-Labs/weft/pull/146), [#148](https://github.com/Moissanite-Labs/weft/pull/148)) showed raw coordinate transfer can improve IID targets yet fail shifted retention and permutation. E11 tests whether null-space projection plus alignment beats those baselines on a toy MLP “cell.”

This rerun supersedes the closed PR [#150](https://github.com/Moissanite-Labs/weft/pull/150): the harness now matches `PREREG.md` (tanh readout, `N_j=256`, new task on logit 3, deterministic probe seeds, rank-1 probe readout correction on `plasmid`, corrected alignment diagnostics, and primary checks on every seed where registered). The earlier loom copy tracked the #150 harness (wrong task index, inflated accuracies); this directory now holds the #201 rerun only.

## Reproduce

```bash
python3 experiments/e11-plasmid-transfer-breaking-through-2026-11/run_e11.py
```

The `commit` field in `results/e11_results.json` is `git rev-parse HEAD` at run time (repository root).

## Pre-registered pass bar vs arms (cross-seed means, 5 seeds)

| Arm | New-task acc | Bar ≥0.80 | Shifted pass (of 4) | Bar ≥3.0 | IID retention | Bar 1.0 | ‖UᵀΔW‖ mean | Bar ≤1e-3 | B train steps |
|-----|-------------|-----------|---------------------|----------|---------------|---------|-------------|-----------|---------------|
| `raw_coord` | 0.617 | fail | 1.8 | fail | 0.60 | fail | n/a | n/a | 0 |
| `perm_taskvec` | 0.636 | fail | 2.8 | fail | 0.80 | fail | n/a | n/a | 0 |
| `null_only` | 0.523 | fail | 4.0 | pass | 1.00 | pass | 1.3e-10 | pass | 0 |
| `plasmid` | 0.727 | fail | 4.0 | pass | 1.00 | pass | 1.2e-10 | pass | 0 |
| `frobenius_gate` | 0.617 | fail | 1.8 | fail | 0.60 | fail | n/a | n/a | 0 |

Bars match `PREREG.md`. `[measured]` Source: `results/e11_results.json` → `pass_bar_table` (certificate bar enforced per seed in `plasmid_primary_verdict`, not on the mean).

## Primary verdict (preregistered plasmid arm)

`[measured]` `plasmid_primary_verdict`: **mixed** (3/6 checks). Passes: shifted retention mean, IID retention on all seeds, `‖UᵀΔW‖_F ≤ 1e-3` on every seed. Fails: new-task mean &lt; 0.80, fewer than 3/5 seeds ≥ 0.80, permuted-sanity gate (new-task acc &lt; 0.95 on **all five** seeds despite full retention probes).

## Overall E11 verdict for #149

**Mixed / primary bars not met.**

- `[measured]` With the **actual new task (logit 3)**, cross-seed **plasmid** reaches mean new-task accuracy **0.727** (rank-1 probe correction helps vs **null_only** at 0.523) but **does not** meet the registered ≥ 0.80 mean or ≥ 3/5 seed rule.
- `[measured]` **Null projection** still gives **perfect shifted retention** and IID retention, with tiny non-interference certificates (~1e-10).
- `[measured]` **Raw coordinate** transfer hurts retention (mean shifted pass 1.8/4) while only modestly moving the new task.
- `[measured]` **`frobenius_gate` is numerically identical to `raw_coord` on every seed** at the preregistered radius (see below); treat retention and new-task numbers for that arm as the raw-coordinate baseline, not as evidence about norm-limited transfer.
- `[measured]` After fixing the permutation correlation indexing, cross-seed activation matching is **moderate** (median correlation ~0.45–0.56; `gramian_alignment_failed: false` on these seeds).
- `[speculative]` Toy MLPs remain a weak stand-in for gauge-scrambled production cells; no scale-up was run (per prereg stop rule).

## `frobenius_gate` (preregistered, non-binding at this R)

`[measured]` Per `PREREG.md`, the arm clips the plastic delta to `‖ΔW‖_F ≤ R` with `R = ‖ΔW_A‖_F` (donor delta Frobenius norm on plastic parameters). The implementation sets `R = min(‖ΔW_A‖_F, R_INVARIANT)` with `R_INVARIANT = 120` (shipped metabolic invariant). Donor delta norms here are ~3–4, far below 120, so **the clip never binds** and **`frobenius_gate` duplicates `raw_coord`** on all seeds and all reported metrics in `results/e11_results.json`. This arm is **not** evidence about whether a tighter Frobenius gate would improve retention; a **binding-gate sweep** (e.g. `R` as a fraction of `‖ΔW_A‖_F`) is left as a separate follow-up experiment.

## Permuted sanity

`[measured]` Known hidden permutation: **IID + all shifted retention probes pass** for `plasmid` on every seed, but **new-task accuracy stays below the registered 0.95 bar on all five seeds** (approximately 0.76–0.86; see `per_seed_permuted_sanity` in JSON). No seed reaches 0.95.

## Nonlinear drift

`[measured]` Post-transfer linearization MAE on the new-task tanh readout is in JSON (`nonlinear_drift_new_task_mae`), computed with per-input first-order grads at the evaluated points (new-task rows are outside `J_keep`).

## Epistemic limits

- Jacobian null-space safety is **first-order** `[derived]`; we report nonlinear drift explicitly.
- Greedy column matching is a minimal Re-Basin stand-in, not full Hungarian / transport.
- No claim about LLM weight surgery, Astra teachers, or production gates.