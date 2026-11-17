# Heddle knob range: how far can a knob be trusted?

## Question

The heddle instrument (`notes/prototypes/heddle/`) lets a person steer a small model with named knobs, pin inputs that must not move, and commit a change only through weft's gate and a behaviour claim. How far does each of those hold: how far can a knob travel before its label is wrong, what does a pin cost, how much change hides between known probes, and does the instrument's forecast agree with the check that follows?

## Status

`complete`

The confirmatory run was made after the preregistration was pushed. Sixteen of seventeen predictions were confirmed in each arm. **One was not in each: H3b in the random arm and H4a in the fitted arm.** Sections marked exploratory were not predicted.

## Preregistration

[PREREG.md](PREREG.md) was committed and pushed in `db4db2f` at 08:07:02 UTC on 17 November 2026. The confirmatory run started at 08:07:11 UTC and ended at 08:08:07 UTC. The results file records the hashes of `study.py` and `heddle.py`, and both equal the ones in the preregistration. `summarise.py` is unchanged since that commit.

Every threshold was set after a pilot on seeds 1 to 4 (`data/pilot.json`). `describe.py` was written after the run. It only tabulates, and what it prints is exploratory.

## How to rerun

Needs Python 3.12 or newer with NumPy. Run from this folder inside a weft-loom checkout: `study.py` imports `notes/prototypes/heddle/heddle.py`.

```
python3 study.py --seeds 1 2 3 4 --out data/pilot.json
python3 study.py --seeds 101 102 103 104 105 106 107 108 109 110 111 112 --out data/results.json
python3 summarise.py data/results.json --json summary.json
python3 describe.py data/results.json
```

Run on one cloud container: Linux x86_64, Python 3.13.18, NumPy 2.5.3. The confirmatory run takes about a minute. The fitted hosts come out of 400 optimiser steps, so on another machine or NumPy build their last digits, and with them every number of that arm, may differ. Each host's weight root is in the results file for comparison. No second machine was tried.

## Results

### The predictions

A prediction is confirmed in an arm when it holds on at least 11 of 12 hosts. The second number is the range of the deciding quantity over the 12 hosts. Source: `summary.json`.

| Prediction | Random hosts | Fitted hosts |
|---|---|---|
| H1a Up to travel 0.6 a treadle's label is right within a factor 1.1 | 12 of 12, 1.03 to 1.09 | 11 of 12, 1.02 to 1.21 |
| H1b At travel 0.9, within 1.25 | 12 of 12, 1.04 to 1.13 | 11 of 12, 1.03 to 1.36 |
| H1c At travel 2.5 the label is off by more than 1.1 | 12 of 12, 1.15 to 1.44 | 12 of 12, 1.10 to 2.79 |
| H2a Two treadles add, within 0.06, up to travel 0.3 | 12 of 12, 0.025 to 0.053 | 12 of 12, 0.017 to 0.043 |
| H2b Within 0.2 at travel 0.9 | 12 of 12, 0.073 to 0.138 | 12 of 12, 0.051 to 0.123 |
| H3a With 4 heddles the pinned inputs move less than 0.1 as much as unpinned | 12 of 12, 0.005 to 0.058 | 12 of 12, 0.010 to 0.049 |
| H3b With 4 heddles, inputs 4 cells from a pin move less than 0.6 as much | **10 of 12**, 0.16 to 0.63 | 11 of 12, 0.25 to 0.69 |
| H3c With 16 heddles the mean share is below 0.7 of its open value | 12 of 12, 0.28 to 0.59 | 12 of 12, 0.30 to 0.60 |
| H4a A move hidden from 4 by 4 probes changes held-out inputs 5 times more than those probes | 12 of 12, 6.1 to 13.3 | **10 of 12**, 4.6 to 12.0 |
| H4b The change on held-out inputs falls at every step from 3 to 10 known probes a side | 12 of 12 | 12 of 12 |
| H4c Hidden from 10 by 10: 64 fresh probes see less than 0.9 of the search's worst | 12 of 12, 0.18 to 0.79 | 12 of 12, 0.13 to 0.81 |
| H5a The worst direction changes outputs at least 4 times more than a typical one | 12 of 12, 5.5 to 6.8 | 12 of 12, 6.1 to 7.6 |
| H5b All 20 random moves at the gate's radius break the claim | 12 of 12 | 12 of 12 |
| H5c The proved radius is 2 to 10 times under the breaking radius, and the proved bound is never exceeded | 12 of 12, 3.3 to 4.6 | 12 of 12, 2.7 to 5.2 |
| H7a No pick with tension below 0.7 snaps | 12 of 12 | 12 of 12 |
| H7b Every pick with tension 1.0 or more snaps | 12 of 12 | 11 of 12 |
| H7c The search's worst input is within 1.25 of the forecast, for every pick | 11 of 12, worst 1.09 to 1.36 | 12 of 12, worst 1.08 to 1.24 |

### The misses

**H3b, random arm.** On seeds 103 and 108 the inputs four cells from a pin moved 0.62 and 0.63 as much as with no pins, against a bar of 0.6. The same reading on fitted seed 102 was 0.69. The pilot range was 0.20 to 0.41, so the bar was set too close to it. Over all 24 hosts the reading runs from 0.16 to 0.69. A pin does hold its neighbourhood back on every host. By how much varies more than four pilot seeds showed.

**H4a, fitted arm.** On seeds 104 and 109 the move hidden from 16 known probes changed held-out inputs 4.59 and 4.62 times more than it changed those probes, against a bar of 5. The pilot range was 7.9 to 13.5. The hidden move is a first-order construction and what the known probes see of it is second order, so the ratio depends on how curved the host is along that one direction.

**Single hosts inside confirmed predictions.** Fitted seed 103: the label factor reached 1.21 at travel 0.6 and 1.36 at 0.9 (H1a, H1b). Random seed 104: one pick's worst input was 1.36 times its forecast (H7c). Fitted seed 102: one pick at tension 1.029 had a worst input of 0.494 and did not snap (H7b).

### What the predictions say together

- **A label holds further than the claim lets a pick go.** Up to travel 0.6 the measured gain of a treadle on held-out inputs is within 1.1 of what the tie-up promised on 23 of 24 hosts. Of the 1,440 forecast picks, none of which presses a treadle further than 0.6, 869 snapped. So on these hosts the knob's label is not what limits a pick. The claim is.
- **The forecast was right at both ends.** Pooled over both arms, 0 of 419 picks with tension below 0.7 snapped, 830 of 831 with tension 1.0 or more snapped, and 39 of 190 in between. The forecast is a first-order reading on 100 probes. The check is a search over 9,600 inputs.
- **A heddle is expensive.** Sixteen pins close 48 of 467 directions, about a tenth, and leave between 0.28 and 0.60 of the named reach.
- **Probes that are known leave room.** The change that fits between the probes falls as they multiply, from about 0.23 at 3 a side to about 0.014 at 10 a side for a move of length 0.3 (medians). For the move hidden from the 10 by 10 grid, 64 probes drawn afterwards see between 0.13 and 0.81 of what the search finds.
- **The ball is the wrong shape here too.** Every random move at the gate's radius of 2.0 broke the claim on every host, and the top shaft breaks it at a radius between 0.07 and 0.19. This repeats the calibration record's H1a and H6d on a different host.

### Exploratory

From `describe.py`. None of this was predicted.

**Re-threading against projecting.** With heddles raised there are two ways to steer. Projecting pushes the old 16-shaft move through the null space of the pins. Re-threading finds the 16 shafts of that null space and ties the treadles to those, which is what the instrument does.

| Heddles | Mean share kept, projected | Mean share kept, re-threaded | Held-out change kept, projected | Held-out change kept, re-threaded | Pin move over unpinned, re-threaded |
|---|---|---|---|---|---|
| 1 | 0.85 to 0.94 | 0.82 to 1.06 | 0.77 to 1.00 | 0.89 to 1.12 | 0.001 to 0.039 |
| 4 | 0.63 to 0.80 | 0.66 to 0.93 | 0.29 to 0.92 | 0.78 to 1.08 | 0.005 to 0.058 |
| 16 | 0.16 to 0.53 | 0.28 to 0.60 | 0.07 to 0.25 | 0.45 to 0.84 | 0.011 to 0.152 |
| 32 | 0.16 to 0.41 | 0.18 to 0.43 | 0.02 to 0.10 | 0.35 to 0.80 | 0.031 to 0.229 |

Ranges over all 24 hosts. Re-threading kept a higher share on 22 of 24 hosts at 4 and at 16 heddles, and on 15 of 24 at 32. It keeps much more of the pick's overall change. It also lets more reach the pins: its moves are longer, and what reaches a pin is second order in the length. At a fixed 16 shafts a share above its open value is possible, because the shed's first 16 shafts are not the open ones.

**The first-order error of a treadle move** (its distance from `J d` on held-out inputs, over its size) has a median over hosts of about 0.03 at travel 0.2, 0.09 at 0.6, 0.14 at 0.9 and 0.4 at 2.5, in both arms.

**The top shaft breaks the claim at about half the first-order radius.** Medians: breaking radius 0.148 (random) and 0.134 (fitted), against `tau / sqrt(lam_max)` of 0.299 and 0.259. The first-order radius is for the root mean square over the probes and the claim is about the worst input.

**The `contrast` treadle is weak on fitted hosts.** Its open share has a median of 0.10 there (0.79 on random hosts). On at least half the fitted hosts it is below the 0.2 floor and so is not in H1.

**The fitted hosts fit.** The error against the target fell from between 1.44 and 2.11 to between 0.044 and 0.089.

## Limits

- **One toy host shape.** 467 weights, tanh units, two-dimensional inputs, three outputs. The inputs can be seen whole and the dispute search can read a lattice of them. Neither is true of a language model.
- **Twelve hosts per arm, one machine, one run.** The fitted arm is fitted to one kind of picture. Thresholds were set on four pilot seeds, and two of them turned out too tight.
- **The claim's limit and the gate's radius are the instrument's defaults**, 0.5 and 2.0. Other values were not tried. H5b in particular depends on the radius.
- **The hidden move is first order** and its length is fixed at 0.3. A stronger adversary would find more room. H4 is a lower bound on what hides.
- **The dispute search is bounded.** "Did not snap" means no input above the limit was found among 9,600.
- **Sixteen shafts and one probe grid.** Shares, and so H1's choice of treadles and H3c, depend on both.
- **No person took part.** Nothing here says whether a person steers better with this instrument, which is the question the note cares about most.
- **H5a, H5b and the bound in H5c restate known results** on a new host. They are checks that this host behaves like the calibration hosts, not new findings.
- Nothing here is a statement about the Plasm cells of the runtime or about Spaceship.

## What is here

| File | What it holds |
|---|---|
| [PREREG.md](PREREG.md) | The design, the measures, the seventeen predictions and the frozen program hashes |
| `study.py` | Builds the hosts and takes every measurement |
| `summarise.py` | States each prediction per host. Frozen with the preregistration |
| `describe.py` | Descriptive tables. Written after the run |
| `data/pilot.json` | Pilot output, seeds 1 to 4 |
| `data/results.json` | Confirmatory output, seeds 101 to 112 |
| `summary.json` | The verdict table, with the seeds that missed |

## Disclosure

Designed, written and run by an AI agent session (Claude) at the request of the repository owner. No human has reviewed it. The preregistration was pushed nine seconds before the confirmatory run started, by the same session, so the order rests on the commit and on the hashes recorded in the results file.
