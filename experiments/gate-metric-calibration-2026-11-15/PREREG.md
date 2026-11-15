# Preregistration: which distance predicts behaviour change?

Written 15 November 2026, before any confirmatory host was trained. It answers the call in weft-loom issue 7 to "preregister a calibration study before running it". The commit that adds this file is pushed before the confirmatory run starts. The derivations are in `THEORY.md`.

## What was seen before this was written

Two pilot hosts for each architecture, seeds 900 and 901. Their outputs are committed in `pilot/`. The test design changed once after the pilot, and the change is listed at the end. No confirmatory seed has been run in any form.

## Design

Two programs, one architecture each.

| | `calib.py` | `calib_tf.py` |
|---|---|---|
| Model | E13 organism, 24 to 96 to 96 to 8, 12,488 weights | two-layer transformer, width 32, 18,839 weights |
| Native behaviour | skills 0 and 1 of an E13 world | `max(a, b)` and `floor((a + b) / 2)` over 23 values |
| Output | 8 real numbers | 23 centred logits at the last position |
| Fit probes | 256 fresh native inputs | 96 native inputs |
| Held-out inputs | 2,048 fresh native inputs, plus 2,048 shifted | the 866 native inputs outside the probes and the attacker's set |
| Drop score and bar | fall in shifted native R2, bar 0.025 (the E13 retention bar) | fall in held-out accuracy, bar 0.025 |
| Radii tested | 0.01 to 30 in eight steps | 0.0001 to 3 in ten steps |
| Local radius `r_loc` | 0.1 | 0.001 |
| Radius for the probe-aware adversary `r_blind` | 1.0 | 0.01 |

Confirmatory hosts: seeds 0 to 11 for each program. Each MLP host has its own task world. Seed streams are listed at the top of each program and are disjoint from the E13 record and from the pilot.

If a host stops on an internal check (for example a transformer that does not reach 0.99 native accuracy), that seed is replaced by the next unused integer from 12 upward, and the README says so.

## Measures

For a move `d` from the trained weights `w0`:

- `r`: its Frobenius length. This is what the shipped gate bounds.
- `fisher`: `||J d|| / sqrt(n m)`, the first-order prediction from the fit probes.
- `probe`: the measured output RMS change on the fit probes.
- `held`: the measured output RMS change on the held-out inputs. This is the target.
- `drop`: the fall in the drop score.
- `cert` (MLP only): the proved upper bound of `THEORY.md`, Theorem 1.

## Moves

Scaled to each tested radius:

- `rand`: five random directions.
- `top`: the top eigenvector of the fit probes' matrix.
- `null`: three random directions inside the null space of the fit probes.
- `grad_native` and `grad_novel`: a gradient step on native data and on the novel skill.
- `adam_novel`: the sign of the novel-skill gradient.
- `flip`: the readout flip direction.
- `dormant` (MLP only): a random move confined to the lowest-score units.

At their own length:

- `perm`: a hidden-unit permutation.
- `flip`: the full readout flip.
- `to_init`: the move back to the initial weights.
- `one_step`: one optimiser step at the training learning rate.
- `finetune_joint`: joint training on native and novel skills.
- `graft` (MLP only): the benign E13 splice.

Searched inside each ball:

- `adv`: an adversary that maximises change on its own inputs (256 or 96 of them) and never sees the fit probes.
- `adv_blind`: an adversary that knows the fit probes, stays in their null space and is penalised for any change on them.

A move counts as **made without sight of the probes** unless it is `top`, `null` or `adv_blind`.

## Predictions

A prediction is **confirmed** for an architecture if it holds on at least 11 of 12 hosts, and **refuted** if it holds on 6 or fewer. In between it is reported as mixed. The counts are computed by `analyse()` in `calib.py`, which is the same code for both programs.

| Id | Statement, per host | MLP | Transformer |
|---|---|---|---|
| H1a | At `r_loc`, `held` along `top` is at least 10 times the median `held` of the random directions | confirmed | confirmed |
| H1b | The permutation is at least 30 times farther than the adversary's breaking radius, and its `held` is at most 1e-9 | confirmed | confirmed |
| H2a | For every move up to `r_loc` made without sight of the probes, `probe / fisher` lies in [1/1.1, 1.1] | confirmed | confirmed |
| H2b | For the same moves, `held / fisher` lies in [0.8, 1.25] | confirmed | confirmed |
| H3a | For the `null` moves at `r_loc`, `fisher` is at most 1e-9 and `held` is at least 1e-6 | confirmed | confirmed |
| H3b | For at least one of the moves `perm`, `graft`, `finetune_joint`, `to_init`, `held / fisher` is below 1/3 or above 3 | confirmed | confirmed |
| H4 | For every move made without sight of the probes, at every radius and at its own length, with `held` at least 1e-6: `held / probe` lies in [0.8, 1.25]. And the permutation's `probe` is at most 1e-9 | confirmed | confirmed |
| H5a | For `adv_blind` at `r_blind`, `held / probe` is at least 10 | confirmed | confirmed |
| H5b | At some tested radius, `adv_blind` shows no more change on the fit probes than the benign graft does, and breaks the bar | confirmed | not tested |
| H6a | The adversary's breaking radius is at most a tenth of the smallest radius at which a random move breaks the bar | confirmed | confirmed |
| H6b | One optimiser step is at least as long as the adversary's breaking radius | confirmed | confirmed |
| H6c | The benign graft passes the E13 joint bar at a distance of at least 20 | at least 10 of 12 | not tested |
| H6d | A random move breaks the bar at radius 10 or less, the smaller shipped radius | confirmed | not tested |
| H7 | The certified radius for a change of 0.05 is at most the radius at which the adversary reaches 0.05. The program stops if any measured change exceeds the proved bound | 12 of 12 | not tested |

The breaking radius is the smallest tested radius at which the drop exceeds the bar. The grid is coarse (about half a decade), so H6a and H6b are statements at that resolution.

## How the result maps onto issue 7

Issue 7 states a pass mark: "one distance predicts behavior change within a stated factor across directions". Its fail mark is that no distance beats Frobenius by that factor, and "then the gate needs a behavior check, not a better norm". The stated factor here is 1.25.

- If H1 and H3 are confirmed, no distance computed from the weights alone passes: Frobenius fails by the anisotropy, and the first-order distance fails on symmetries, on large moves and inside its null space.
- If H4 is also confirmed in both architectures, the probe check passes the mark for every move made without sight of the probes. The reading is then the issue's fail-mark branch: a behaviour check, not a better norm.
- If H5 is confirmed, that reading carries a condition: the probes must be unknown to whoever proposes the move.
- If H6a and H6b are confirmed, no radius is both a behaviour guarantee and wide enough for one training step.
- If H4 is refuted in either architecture, neither branch holds and the record says so.

## Reported without a prediction

Per host and as medians:

- `sqrt(lam_max)`, the mean eigenvalue, the anisotropy and the effective rank.
- The breaking radius of each class, and the safe size of each class at a change of 0.05.
- The second-order change of the `null` moves on the fit probes, and their first-order leak onto held-out inputs.
- The ratio of attack radius to certified radius.
- `held / probe` for `top`.

These are descriptive. Anything else found in the data is exploratory and will be labelled so.

## What this cannot show

Two small models on synthetic tasks. One probe-set size per architecture. The adversaries are gradient searches, so a breaking radius is an upper bound on the true one.

The transformer is trained on its whole finite input space. "Held-out" there means unseen by the predictor, not unseen in training.

Nothing here is a statement about the Plasm cells of the runtime, whose moves are far smaller.

## Change of design after the pilot

The first pilot counted `top` among the moves made without sight of the probes. It is not: it is the top eigenvector of the fit probes' own matrix. On one transformer pilot host its change on held-out inputs was 0.63 of its change on the probes. The worst direction for 96 probes is partly specific to them.

So `top` was moved to the probe-built group. The adversary that uses its own inputs (`adv`) took its place in H2 and H4. H1a still uses `top`, where the effect makes the test harder to pass.

The null-space basis was also rebuilt from an eigenvalue decomposition. The first version did not handle the dependent rows of centred logits.

## Programs as frozen

The pilot outputs in `pilot/` were produced by exactly these files, and the confirmatory run uses them unchanged. Each results file records the hash of the program that wrote it.

```
1ac3612de1ec566b397031f2aa1000afd5afea8a6f936b10c8a1d742c2fa18bf  calib.py
ad83c21d6d6215052d23ae162adfa6deda5958553e20a2ccbcaff93cfe186f4c  calib_tf.py
```

Commands for the confirmatory run:

```
python3 calib.py --seeds 0 1 2 3 4 5 6 7 8 9 10 11 --out results.json
python3 calib_tf.py --seeds 0 1 2 3 4 5 6 7 8 9 10 11 --out results_tf.json
```

## Disclosure

Written and run by an AI agent session with human oversight.
