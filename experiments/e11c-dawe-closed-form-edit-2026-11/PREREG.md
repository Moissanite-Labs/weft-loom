# weft-loom E11c (draft): a DAWE-style edit against the E11/E11b retention trade-off

Author: grk-tensor · 2026-11-17 (America/Chicago) · Status: **design and preregistration draft**, finalized against qalam's substance call (7:33 PM CT).
**Nothing has been run on the toy.** No arm, diagnostic, or rank computation has been executed, so the preregistration stays clean.
Name: **E11c**. It continues the E11 → E11b retention lineage on the same toy. E12–E16 and E18 are taken on `main`.
Labels: CITED = opened this session · CITED (qalam relay) = reported by qalam, not independently verified · SPECULATION = design proposal · OPEN = for qalam.

## 0. Sources (re-checked against current `main` and both merge commits; raw.githubusercontent.com only, no gh/API/clone)
Merge commits, CITED (qalam relay):
- **#33 (E11b)** merged as `41cdcf62854dd3c93319ea2663e18324a8de267d`.
- **#34 (E11 prereg-faithful port)** merged as `6b840ee0e3a95f055f91cdd0b5812f005c6c3591`.

I could not open the PR pages themselves (no-GitHub rule). The file contents at those SHAs are consistent with that order: `experiments/e11b-…/README.md` returns 404 at `6b840ee0` and 200 at `41cdcf62`.

| Source | `main` | `41cdcf62` | `6b840ee0` | vs my Nov 14 local copy (`4208cda`) |
|---|---|---|---|---|
| `experiments/weight-space-2026-11-12/README.md` | 200 | 200 | 200 | **byte-identical**, no change |
| `experiments/astra-family-teachers-2026-11-12/README.md` | 200 | 200 | 200 | **byte-identical**, no change |
| `notes/scwsp-directional-gate.md` | 200 | 200 | 200 | **byte-identical**, no change |
| `experiments/e11-…/PREREG.md` (E11 prereg) | 200 | 200 | 200 | **byte-identical**, unchanged since 2026-11-13 |
| `experiments/e11-…/README.md` | 200 | 200 | 200 | **changed**: now the #201 prereg-faithful rerun (§2) |
| `experiments/e11-…/run_e11.py` | 200 | — | 200 (= main) | **changed** (the #201 harness) |
| `experiments/e11b-…/{README.md, PREREG.md, run_e11b.py, results/e11b_results.json}` | 200 | 200 | 404 | not in the local copy |
| `experiments/README.md` (index) | 200 | 200 | 200 | changed: E11b row added at `41cdcf62` / main |

- **Unreachable:** the PR #33 and #34 pages and their review threads, and any weft (not weft-loom) PRs that the records link (#146, #148, #150, #201, issue #149).
- For the weight-space experiment I re-read only the README files, not their data files.

## 1. Folded-in weight-space work (re-checked: unchanged on main)
- **`weight-space-2026-11-12`**: a teacher read raw weights and proposed edits.
  - On the toy MLP, the teacher proposed `fc2.weight.flip(0)` and `fc2.bias.flip(0)`, an output-layer flip. Accuracy went 0.9805 → 0.0195 on the same inputs, with no held-out split.
  - TinyStories-1M row-scale edits "did not produce a reliable fix".
  - The NC1 negative-control suite: no confabulation on noise, and the teacher refused to edit on contradictory stats.
  - Lesson for E11c: an output-row edit can look dramatic while saying nothing about shared representations. That is the reason for the CONTROL rule in §4.
- **`astra-family-teachers-2026-11-12`**: can a teacher model make persistent numerical edits to small policy cells that transfer to related siblings? (Four studies, per the experiments index.) It is the origin of the 5-seed habit and the frozen-core partition that E11 uses.
- **`notes/scwsp-directional-gate.md`** (SC-WSP):
  - The input-side null-space construction keeps `dW·K0ᵀ ≈ 0` for preserved keys `K0`, measured at `3.68e-15` on the prototype (with a random `K0`, not harvested keys).
  - Weft's live gate is the Frobenius ball `‖W_cand − W_base‖_F ≤ R_INVARIANT = 120`.
  - The note proposes adding `‖ΔW·K0ᵀ‖_F ≤ τ` as a second gate.
  - **In E11c this is the preservation term of the MAIN arm** (§4), in the function-space (Jacobian) form E11 already registered.

## 2. What E11 and E11b established (CITED, current main)
- **Substrate** (`run_e11.py`, `run_e11b.py`; PREREG unchanged):
  - input 8-D `U(−1,1)`, 16 ReLU hidden units, of which units 0–3 are a frozen core
  - 4 tanh logits: kept tasks 0–2, **new task = logit 3**; labels `sign(x·w_t + b_t)`
  - `x_train` = 600 inputs (seed+10000); `x_jac` = 256 inputs (seed+10001); new-task eval `x_new` = 512 (seed+5000); retention probes are 512 each
  - seeds `17, 29, 43, 101, 202`
  - cell A = kept tasks then the new task; cell B = kept tasks only
- **E11** (#201 rerun, cross-seed means; the Nov 14 local copy showed the earlier #150 numbers, which had the wrong task index):
  | Arm | New-task acc | IID retention rate |
  |---|---|---|
  | `raw_coord` | 0.617 | 0.60 |
  | `perm_taskvec` | 0.636 | 0.80 |
  | `null_only` (A's delta projected into `ker(J_keep)`) | 0.523 | 1.00 |
  | `plasmid` (alignment + null projection + a **rank-1 least-squares fit of B's row-3 readout to A's outputs**) | 0.727 | 1.00 |
  | `frobenius_gate` | identical to `raw_coord` at the registered radius | |
- **E11b** (binding Frobenius clip `f·‖Δ‖`):
  | Setting | New-task acc | IID retention rate |
  |---|---|---|
  | `raw_coord` | 0.617 | 0.60 |
  | `f = 0.1` | 0.510 | 1.0 |
  | `f = 0.25` | 0.509 | 1.0 |
  | `f = 0.5` | 0.554 | 1.0 |
  | `f = 0.75` | 0.599 | 0.80 |
  | `f = 1.0` | identical to `raw_coord` | |
- **No E11b clip setting passes all three of E11b's bars** (new-task ≥ 0.80, shifted ≥ 3 of 4, IID 1.0). None of the existing E11 or E11b arms passes E11c's two bars (§3) either.

## 3. Preregistered bars (exactly two; both must hold)
1. **New task:** new-task accuracy on B, averaged across the 5 seeds, **≥ 0.80**. This is computed on `x_new` exactly as E11 and E11b do.
2. **Kept-task retention:** on **every** seed, **each** of the 3 kept tasks drops by **≤ 0.10** in accuracy on the IID probe, relative to B before the edit.

An arm **passes** iff bars 1 and 2 both hold. The shifted-probe pass count, E11's per-seed "≥ 3/5 seeds ≥ 0.80" rule, `‖Δ‖_F`, the Weft ball-gate check (`‖Δ‖_F ≤ 120`), the number of weights changed, and E11-style nonlinear drift are all **reported, not gating**.

## 4. Arms

**Shared fitting rules.**
- Edits are fitted only on `x_train` (600) plus `x_jac` (256). `x_new` and the probe draws are never used for fitting or selection.
- The one selected hyperparameter (`λ_p`) is chosen on a new **validation draw**: 512 inputs at seed+20000, pre-declared here.
- The DAWE solver rule is `λ = 0.01 · mean diag` of the Gram matrix, as in DAWE's committed edit scripts.
- The DAWE-style target at a failing decision is `r(x) = clip(atanh(0.9)·y₃(x) − z₃(x), −3, 3)`, where `z₃` is B's pre-tanh new-task logit. At non-failing `x_train` points the target is 0, which matches DAWE's zero-target preserve points.
- The failing set is `F = {x ∈ x_train : sign(tanh z₃(x)) ≠ y₃(x)}`.

### MAIN: `dawe_hidden_scwsp` (the only arm whose pass counts as evidence)
- **Edits:** only B's **shared plastic hidden layer**, `w1[4:16, :]` and `b1[4:16]` (108 weights). It touches no output row.
- **Data attribution:** `G = ∂z₃/∂θ_h` at `x_train`. Analytically, for an active unit j: `w2[3,j]·x` for `w1[j,:]` and `w2[3,j]` for `b1[j]`.
- **Preservation (SC-WSP, in E11's Jacobian form):** `J = ∂ logit_k / ∂θ_h` for k ∈ {0,1,2} at `x_jac` (768 × 108). This is the same definition as E11's `J_keep`, restricted to hidden parameters.
- **Solve:** `Δθ_h = (GᵀG + λ_p JᵀJ + λI)⁻¹ Gᵀ r`, with `λ_p ∈ {0.1, 1, 10, 100, 1000}`.
  - **Selection rule** (pre-declared): on the validation draw, take the largest new-task accuracy subject to every seed's kept-task drops ≤ 0.10. Ties go to the larger `λ_p`.
  - The choice is frozen in `E11c/FROZEN.json` before any `x_new` or probe evaluation.
- **Reported companion `dawe_hidden_scwsp_exact`:** the hard projection `Δθ_h = P Gᵀ(G P Gᵀ + λI)⁻¹ r` with `P = I − J⁺J`. This is the `λ_p → ∞` limit.
- **Pre-declared diagnostic, recorded first:** the numerical rank of `J` restricted to `θ_h`, using E11's tolerance. With 768 rows over 108 parameters, the exact null space may be **trivial** (SPECULATION). If it is, the exact arm is the zero edit and is reported as such.
- **Pre-declared interpretation:**
  - A MAIN pass means a data-attributed closed-form edit of **shared** weights met the new-task bar without breaking kept tasks. That is the claim E11c tests.
  - A MAIN fail that is new-task-limited means B's hidden layer can't be bent toward task 3 under the preservation constraint.
  - A MAIN fail that is retention-limited at every `λ_p` means the first-order preservation term doesn't hold under ReLU switching (report nonlinear drift).

### CONTROL: `row3_only`, labelled **retention-by-construction**
- **Edits:** only B's new-task output row `w2[3]` and `b2[3]` (17 weights). Ridge fit on B's hidden states `h(x)` over `x_train`, with the targets above.
- Kept-task logits 0–2 and the hidden layer are untouched, so **bar 2 is guaranteed by construction**.
- **A pass on this arm counts as ZERO evidence** about the retention trade-off. It only shows that task 3 is linearly decodable from B's existing features.
- It is reported as a ceiling for output-only edits, alongside E11's `plasmid`, which already includes a row-3 least-squares fit.
- **It may not be cited as "DAWE beats the trade-off" in any summary.**

### DAWE-faithful variant: `dawe_rows_faithful`
- **Matches what DAWE edited:** a few output rows (in DAWE, two tied embedding/output rows), fitted with DAWE's exact ridge rule and zero targets at preserve decisions.
- **Edits:** the readout rows `w2[k], b2[k]` for k ∈ {3, k₁, k₂}, where k₁ and k₂ are the 2 kept rows with the largest `|cos(w2[k], w2[3])|` in B. The rule is pre-declared. Targets are `r(x)` on row 3 and **0 on the kept rows** at all `x_train` points and at kept-task decision points.
- **Pre-declared structural note (SPECULATION; to be confirmed by code review, not by a run):**
  - The E11 toy's output rows are **not tied** to any input-side parameter.
  - Multi-output ridge decouples by output column, so zero targets give a zero edit on k₁ and k₂, and this variant should equal `row3_only`. That is **retention-by-construction, zero evidence**.
  - Registered identity check: its predictions must equal `row3_only` within 1e-12. If they don't, that is a bug.
- **To actually mirror DAWE's tied matrix**, the substrate needs a tied variant, for example an output row shared with an input embedding. That would leave the E11 lineage (OPEN question 2).

### Baselines (rerun from the pinned #201 / E11b code; must reproduce the published means as a harness check)
- `raw_coord`
- `null_only`
- `plasmid`
- `perm_taskvec`
- E11b `frobenius_f{0.1, 0.25, 0.5, 0.75, 1.0}`

A mismatch flags harness drift, as E11b's own control-match rule does.

### Controls for MAIN
- **`rand_hidden`:** a same-norm random direction in `θ_h`, projected the same way at the selected `λ_p` (3 draws).
- **`bias_hidden`:** only `b1[4:16]` edited (12 weights), by the same solver. This tests whether a state-independent shift explains the result, which is DAWE's own missing unconditional-bias control.

MAIN's new-task accuracy must exceed both controls on ≥ 4 of 5 seeds, with the sign test reported. Otherwise a MAIN pass is downgraded to "not attributable to the data-attributed direction".

## 5. Outputs
- Script `run_e11c.py`, reusing the #201 / E11b functions unchanged (imported, not copied).
- Results in `results/e11c_results.json`: per seed and per arm, new-task accuracy, per-kept-task IID drop, shifted pass count, `‖Δ‖_F`, weights changed, ball-gate pass, nonlinear drift, `J|θ_h` rank, selected `λ_p`, and validation scores.
- Tags as in E11/E11b: `[measured]`, `[derived]`, `[hypothesis]`, `[speculative]`.
- The PREREG is committed before `run_e11c.py` is executed. Stop rule: if NumPy or the #201 harness can't run, commit the prereg and script only.

## 6. Open questions for qalam
1. **Confirmation seeds:** should a MAIN pass also be required on 5 fresh seeds (proposal `303, 404, 505, 606, 707`), or stay with the E11 five?
2. **Tied substrate:** should E11c add a tied-output variant so the DAWE-faithful arm can carry evidence, or keep it as a declared identity check on the E11 toy?
3. **E11's `plasmid` and the null space:** `plasmid` already contains a row-3 readout fit, and `ker(J_keep)` over *all* plastic parameters includes the row-3 readout, which kept logits don't depend on. So part of E11's "perfect retention" may itself be by construction (SPECULATION). Should E11c add a reported diagnostic splitting `null_only`'s delta into its row-3 and hidden parts?
4. **MAIN target:** labels (as drafted), or donor A's outputs, to keep the horizontal-transfer framing? Using labels makes MAIN a data-attributed edit, not a transfer.
5. **Unresolved confound:** E11b notes that structure B shares through the task geometry "may couple retention probes to the transfer delta". That still applies. Should it be addressed before E11c, or carried as a caveat?
