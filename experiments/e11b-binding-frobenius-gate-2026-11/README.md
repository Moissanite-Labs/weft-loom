# E11b — Binding Frobenius gate sweep

Status: `[measured]` complete, 2026-11-18.  
Parent: [E11](../e11-plasmid-transfer-breaking-through-2026-11/).  
Harness lineage: [weft#201](https://github.com/Moissanite-Labs/weft/pull/201).  
Preregistration: `PREREG.md` (committed before results).  
Runner: `run_e11b.py`.  
Raw JSON: `results/e11b_results.json`.

## Reproduce

```bash
python3 experiments/e11b-binding-frobenius-gate-2026-11/run_e11b.py
```

## Registered sanity checks

| Check | Result |
|-------|--------|
| `f = 1.0` ≡ `raw_coord` every seed | **PASS** `[measured]` |
| `post_clip_norm` non-decreasing in `f` | **PASS** `[measured]` |
| Clip bound on all `f < 1` | **PASS** (clip rate 1.0) `[measured]` |

## Per-R results (cross-seed means, 5 seeds)

`[measured]` Source: `results/e11b_results.json` → `aggregate_cross_seed`.

| R fraction | Clip bound rate | Mean post-clip ‖Δ‖_F | New-task acc | Bar ≥0.80 | Shifted pass | Bar ≥3 | IID rate | Bar 1.0 | Verdict |
|------------|-----------------|----------------------|--------------|-----------|--------------|--------|----------|---------|---------|
| `raw_coord` | — | — | 0.617 | fail | 1.8 | fail | 0.60 | fail | **OPEN** (retention failure; new-task below bar) |
| 0.10 | 1.00 | 0.357 | 0.510 | fail | 4.0 | pass | 1.00 | pass | **OPEN** (retention fixed; new-task still low) |
| 0.25 | 1.00 | 0.893 | 0.509 | fail | 4.0 | pass | 1.00 | pass | **OPEN** |
| 0.50 | 1.00 | 1.787 | 0.554 | fail | 4.0 | pass | 1.00 | pass | **OPEN** |
| 0.75 | 1.00 | 2.680 | 0.599 | fail | 3.4 | pass | 0.80 | fail | **OPEN** (IID mixed) |
| 1.00 | 0.00 | 3.573 | 0.617 | fail | 1.8 | fail | 0.60 | fail | **REPRODUCED** (= `raw_coord`; non-binding control) |

**Verdict key (prereg comparative bars only):** pass/fail is factual against E11 thresholds; **REPRODUCED** = registered prediction matched; **OPEN** = no registered win/loss claim; none of the arms meet the full E11 new-task bar.

### Control match

`[measured]` **REPRODUCED:** `f = 1.0` matches `raw_coord` on every seed for new-task accuracy and shifted probe count (`sanity_checks.f1_matches_raw_coord_every_seed`).

## Headline finding

`[measured]` A **binding Frobenius clip monotonically trades new-task transfer for retention**: as `f` decreases from 1.0 to 0.1, mean new-task accuracy falls (0.617 → 0.510) while shifted retention rises (1.8 → 4.0) and IID retention reaches 1.0 for `f ≤ 0.5`.  
`[interpretation]` Norm limiting **does not** recover the E11 new-task bar (0.80) at any tested `f`; it **does** remove the harmful retention pattern seen at full-norm `raw_coord` transfer. There is no `f` in `{0.1,…,1.0}` that simultaneously passes all three comparative bars.

## Curve (facts vs interpretation)

| Observation | Tag |
|-------------|-----|
| New-task acc increases with `f` (0.51 → 0.62) | `[measured]` |
| Shifted pass decreases with `f` (4.0 → 1.8) | `[measured]` |
| Post-clip norm scales linearly with `f` (≈ `f · ‖Δ_donor‖`) | `[measured]` |
| Tighter clip “buys” retention at cost of skill transfer | `[interpretation]` |
| Optimal `f` for joint bars on this toy | `[speculative]` none found in sweep |

## Caveats

- **E11 recipient confound:** Early E11 commits scored kept **task 2** instead of the new task (logit 3); [#201](https://github.com/Moissanite-Labs/weft/pull/201) fixes evaluation. This E11b run uses the #201 harness (new task on logit 3). Any residual structure in B from shared task geometry is **unchanged** from E11 and may couple retention probes to the transfer delta. `[derived]`
- Toy MLP, five seeds, CPU NumPy only; no claim about production `R_INVARIANT` or plasmid arms.

## Relation to E11 non-binding `frobenius_gate`

`[measured]` E11's original gate set `R = min(‖Δ‖, R_INVARIANT)`, which never clipped at ‖Δ‖ ≈ 1.4–3.6. E11b shows that **when clipping is forced**, behavior **diverges** from `raw_coord` unless `f = 1.0`.