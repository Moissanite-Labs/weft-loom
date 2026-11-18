# Preregistration: E11b — binding Frobenius gate on horizontal transfer

Date: 2026-11-18 UTC  
Status: Preregistered **before** any E11b numerical outcomes in this directory.  
Parent: [E11](../e11-plasmid-transfer-breaking-through-2026-11/) (`experiments/e11-plasmid-transfer-breaking-through-2026-11/`).  
Source harness: [Moissanite-Labs/weft#201](https://github.com/Moissanite-Labs/weft/pull/201) (prereg-faithful E11 rerun).

## Motivation

`[derived]` In E11, the `frobenius_gate` arm clips the donor plastic delta to `‖Δθ‖_F ≤ R`. The registered implementation set `R = min(‖Δθ_A‖_F, R_INVARIANT)`, which equals the full delta norm on every seed in the toy pilot, so the clip **never binds** and `frobenius_gate` is identical to `raw_coord`. That leaves the substantive question unanswered: **when the Frobenius ball actually truncates the transfer, does the new-task gain survive, improve retention, or disappear?**

E11b is a follow-up experiment that holds the E11 substrate fixed and sweeps binding radii.

## Epistemic framing

Tags: `[measured]`, `[derived]`, `[hypothesis]`, `[speculative]`. Outcomes that contradict the hypothesis are first-class results.

## Hypothesis

`[hypothesis]` **Norm-limited coordinate transfer** (Frobenius clip at fraction `f` of the donor plastic delta norm) trades off new-task accuracy against kept-task retention under shift. At sufficiently small `f`, both new-task gain and harmful retention drift should shrink; at `f = 1.0` the arm should reproduce `raw_coord`. The **direction** of the trade-off (monotone vs non-monotone in `f`) is not pre-committed.

## Toy substrate (unchanged from E11 #201)

- Same architecture, core freeze, training schedule, Jacobian size `N_j = 256`, tanh readout, new task on **logit index 3** (`NEW_TASK = 3`).
- **Cell A:** kept tasks then new-task fine-tune only.
- **Cell B:** kept tasks only; never trained on the new task.
- **Pairing:** `cross_seed` only (independent A/B inits per seed).
- **Seeds:** `17, 29, 43, 101, 202` (same five as E11).

## Arms (this experiment)

| Arm | Definition |
|-----|------------|
| `raw_coord` | Reference: add donor plastic delta in B coordinates (no clip). |
| `frobenius_f{f}` | Add `clip(Δθ, R)` with `R = f · ‖Δθ_A‖_F` for `f ∈ {0.1, 0.25, 0.5, 0.75, 1.0}`. |

`f = 1.0` is the **non-binding control**; it must match `raw_coord` within floating-point tolerance.

No `null_only`, `plasmid`, or `perm_taskvec` arms in this sweep (reported only via linkage to E11 for context).

## Registered outputs per (seed, f)

- `delta_frobenius_plastic`: donor ‖Δθ‖_F.
- `r_gate`: `f · delta_frobenius_plastic`.
- `clip_bound`: true iff pre-clip norm `> r_gate` (clip active).
- `post_clip_norm`: ‖Δθ_clipped‖_F after clip.
- Same retention and new-task metrics as E11: new-task accuracy, IID all-kept pass, shifted probe pass count (max 4), retention_by_probe, nonlinear_drift_new_task_mae.

## Pass bars (carried from E11 secondary / comparative tables)

Applied per `frobenius_f{f}` aggregate over cross-seed runs:

| Metric | Pass threshold |
|--------|----------------|
| New-task accuracy mean | ≥ 0.80 |
| Shifted retention mean | ≥ 3.0 of 4 probes (all kept tasks each) |
| IID retention | 3/3 kept tasks within 0.10 acc drop on IID probe for every seed |

`raw_coord` reported against the same bars for direct comparison.

## Sanity checks (must pass or experiment is invalid)

1. **`f = 1.0` ≡ `raw_coord`:** For every seed, new-task accuracy and shifted pass count match `raw_coord` within `1e-12` on metrics that are deterministic; post-clip norm equals pre-clip norm; `clip_bound = false`.
2. **Binding monotonicity of norm:** For fixed seed, `post_clip_norm` is non-decreasing in `f` and never exceeds `delta_frobenius_plastic`.
3. **Clip flags:** `clip_bound = true` for all `f < 1.0` unless `delta_frobenius_plastic = 0`.

## Control comparison to E11

`[derived]` We compare the `f = 1.0` arm to published E11 #201 `raw_coord` means where available. A mismatch flags harness drift, not a biological claim.

## Caveats (pre-registered)

- **Recipient confound from E11:** In early E11 runs, evaluation mistakenly targeted kept **task 2** instead of the new task; the #201 harness fixes that. Residual coupling may still leave B's representation partially aligned with task structure unrelated to the transfer delta — noted in the report, not removed here.
- Toy MLP only; no scale-up.

## Artifacts

- Script: `run_e11b.py`
- Results: `results/e11b_results.json`
- Report: `README.md` (written after results commit)

## Stop rule

If NumPy or the E11 harness cannot run in the execution environment, commit prereg + script only and stop with a missing-deps report.

Signed-off-by: Mithrax Agent <agent@moissanite.dev>