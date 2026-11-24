# Preregistration: how far can a knob be trusted?

Written 17 November 2026, before any confirmatory host was built. The commit that adds this file is pushed before the confirmatory run starts. The idea being tested is in the design note `notes/heddle-steering-instrument.md`, and the code under test is the prototype in `notes/prototypes/heddle/`.

## What was seen before this was written

Four pilot seeds, 1 to 4, in both arms. Their output is `data/pilot.json`, committed with this file, written by exactly the programs listed at the end. Every threshold below was set after looking at it, so on the pilot all seventeen predictions hold on all eight hosts. That is how they were chosen and it is not evidence. Seed 7 is the instrument's default cloth and was used throughout development. No confirmatory seed has been run in any form.

## Design

One program, `study.py`. One host shape: the three-layer network of the calibration theory (`experiments/gate-metric-calibration-2026-11-15/THEORY.md`, Theorem 1), with tanh units, 8 fixed input features of a point of the unit square, 16 and 16 hidden units, 3 outputs. 467 weights.

| | |
|---|---|
| Arms | `random`: the host as initialised from its seed. `fitted`: the same host after 400 Adam steps towards a striped target picture |
| Confirmatory hosts | seeds 101 to 112 in each arm |
| Fit probes | a 10 by 10 grid of inputs, 300 output rows, fewer than the 467 weights |
| Held-out inputs | a 31 by 31 grid. No coordinate is shared with the fit grid |
| Shafts | the first 16 eigen-directions of `G = J'J/(n m)` on the fit probes |
| Treadles | five named output patterns (`warm`, `light`, `tilt`, `contrast`, `check`), each tied to the 16 shafts by least squares |
| Claim | no input changes by more than `tau = 0.5` (root mean square over the three outputs) |
| Gate | weft's baseline-relative gate with radius 2.0 |

If a host stops on an internal error, that seed is replaced by the next unused integer from 113 upward, and the README says so.

## Measures

Travel is in units of behaviour: one unit of travel along a shaft is the weight move whose first-order root-mean-square output change on the fit probes is 1.

- **Promised gain** of a treadle move: the first-order gain along the treadle's pattern on the fit probes, `<J d, c> / <c, c>`.
- **Measured gain**: the same quantity for the real output change on the held-out inputs, with the pattern evaluated there.
- **Label factor**: the larger of measured over promised and promised over measured. Read only for treadles whose share is at least 0.2, both signs of travel.
- **Share** of a treadle: the squared cosine between the output change of its move and its pattern, to first order on the fit probes. For a tie-up move this is the part of the pattern the shafts can carry.
- **Superposition error** of two treadles at one travel: `rms(change(A and B) - change(A) - change(B)) / rms(change(A and B))` on the held-out inputs, for three fixed pairs.
- **Heddles**: 1, 4, 16 and 32 pinned inputs drawn from the host's seed on the 64 by 64 pin lattice. The loom is threaded around them: the 16 shafts are those of `G` restricted to the null space of the pins' Jacobian. The move is all five treadles at travel 0.15. "Unpinned" is the same treadling with no pins.
- **Hidden move**: a move of length 0.3 inside the null space of a known probe grid's Jacobian, along the direction that changes a 24 by 24 grid most, by power iteration. Known grids of 3, 4, 6, 8 and 10 a side.
- **Fresh probes**: 64 inputs derived from the hash of the candidate's weight root and claim, so after the candidate is fixed.
- **Search's worst**: the largest per-input change found by the bounded dispute search (a 96 by 96 lattice, then a climb from the four best cells).
- **Tension** of a pick: the larger of its distance from the baseline over the gate's radius and its first-order worst-probe change over `tau`. A pick **snaps** when the search's worst exceeds `tau`.
- **Forecast picks**: 60 per host, each one to three treadles with travels drawn uniformly from -0.6 to 0.6.

## Predictions

A prediction is confirmed in an arm when it holds on at least 11 of the 12 hosts. Each is stated so that it can fail. `summarise.py`, frozen with this file, is the only code that reads the results for verdicts.

| | Prediction | Pilot range of the deciding number |
|---|---|---|
| H1a | Up to travel 0.6 the label factor is at most 1.1 | 1.029 to 1.063 |
| H1b | At travel 0.9 it is at most 1.25 | 1.043 to 1.110 |
| H1c | At travel 2.5 it is above 1.1: the label does stop holding | 1.125 to 1.654 |
| H2a | Up to travel 0.3 the superposition error is at most 0.06 | 0.023 to 0.044 |
| H2b | At travel 0.9 it is at most 0.2 | 0.065 to 0.125 |
| H3a | With 4 heddles the pinned inputs move less than 0.1 as much as unpinned | 0.008 to 0.041 |
| H3b | With 4 heddles, inputs 4 lattice cells from a pin move less than 0.6 as much as unpinned | 0.20 to 0.41 |
| H3c | With 16 heddles (48 of 467 directions closed) the mean share of `warm`, `light`, `tilt` and `contrast` is below 0.7 of its open value | 0.42 to 0.57 |
| H4a | A move hidden from a 4 by 4 grid changes the held-out inputs at least 5 times more than it changes those probes | 7.9 to 13.5 |
| H4b | The change on held-out inputs falls at every step from 3 to 4 to 6 to 8 to 10 known probes a side | all eight hosts |
| H4c | For the move hidden from the 10 by 10 grid, the largest change among 64 fresh probes is below 0.9 of the search's worst | 0.13 to 0.79 |
| H5a | `kappa = sqrt(lam_max P / trace(G))` is at least 4 | 5.9 to 7.7 |
| H5b | All 20 random moves of length 2.0, the gate's radius, break the claim | 20 of 20 on all |
| H5c | The proved radius is 2 to 10 times below the radius at which the top shaft breaks the claim, and the proved bound is never exceeded | 3.6 to 5.0 |
| H7a | No forecast pick with tension below 0.7 snaps | 0 of 163 |
| H7b | Every forecast pick with tension 1.0 or more snaps | 256 of 256 |
| H7c | For every forecast pick the search's worst is within a factor 1.25 of the forecast | worst factor 1.08 to 1.17 |

The margins are thin on H1c (one pilot host at 1.125 against 1.1), H2a (0.044 against 0.06) and H7c (1.17 against 1.25). A miss on any of them would not be a surprise.

## What follows from the construction, and what does not

- H1a and H2a at small travel are Taylor's theorem. How far they hold is the measurement.
- H3a: the first-order change at a pin is zero by construction. What is measured is the second-order leak, against the first-order change without pins.
- H5c: "never exceeded" is Theorem 1 of the calibration theory, with slope bound 1 for tanh. A violation would be a bug in the port, not a finding. The factor between the proved and the breaking radius is a measurement.
- H5a and H5b restate the calibration record's H1a and H6d on a different host. They are here to check that this host shows the same geometry, not as new claims.
- H7 compares a first-order forecast on 100 probes with a search over 9,600 inputs. Nothing in the construction makes them agree.

## Also reported, without a prediction

- The share each treadle keeps under 1, 4, 16 and 32 heddles, re-threaded and when the old move is merely projected.
- The change on held-out inputs of the heddle moves, and the leak one cell from a pin.
- The first-order relative error of every treadle move.
- The radius at which the top shaft breaks the claim, against `tau / sqrt(lam_max)`.
- The fit error of the fitted hosts before and after training.

These are descriptive. Anything else found in the data is exploratory and will be labelled so.

## What this cannot show

One small network shape, smooth units, two-dimensional inputs, untrained or fitted to one kind of picture. The inputs can be seen whole, which no language model allows. The hidden move is a first-order construction, so the room it finds is a lower bound on what a better adversary would find. The dispute search is bounded: "no input found" is a sampled reading. Sixteen shafts and one probe-set size. One machine.

Nothing here is a statement about the Plasm cells of the runtime, about language models, or about people using the instrument. No person took part.

## Programs as frozen

The pilot output was produced by exactly these files, and the confirmatory run uses them unchanged. Each results file records the hashes of the first and the third.

```
06f17ce7a700f22dcc51b31b8f319fa64edee7e1a12117c3b03af168dcc273b7  study.py
4a3eb82b137892545ef2eb6dd7129f81830eb11cad028768c2930f5df168b528  summarise.py
7dee84700fc2eae176739b2734894b0f9545d72afa97cb226e344115f4a60858  ../../notes/prototypes/heddle/heddle.py
```

## Disclosure

Designed, written and run by an AI agent session (Claude) at the request of the repository owner. No human has reviewed it.
