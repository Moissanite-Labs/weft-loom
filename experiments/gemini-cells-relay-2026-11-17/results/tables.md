# Tables written by analyze.py from the run logs

Replicates complete in all five arms: [0, 1, 4]. Runs left out: solo-pair-r2, twin-fixed-builder-r2, twin-free-collective-r2, twin-free-rival-r2.

## Runs

| Run | Baseline A, B | Outcomes by turn | Exam visible A, B | Exam held-out A, B | Calls | Dollars |
|---|---|---|---|---|---|---|
| solo-pair-r0 | 0.587, 0.480 | KKNNNN | 0.990, 0.990 | 0.583, 1.000 | 465 | 0.79 |
| solo-pair-r1 | 0.551, 0.373 | KKKNNN | 0.944, 0.986 | 0.917, 1.000 | 477 | 0.66 |
| solo-pair-r4 | 0.471, 0.472 | KKNKNN | 0.981, 0.861 | 1.000, 1.000 | 493 | 0.72 |
| twin-fixed-builder-r0 | 0.546, 0.496 | KKKKNN | 0.944, 0.831 | 1.000, 1.000 | 564 | 0.86 |
| twin-fixed-builder-r1 | 0.619, 0.595 | KKRNKR | 0.939, 0.934 | 1.000, 1.000 | 634 | 0.83 |
| twin-fixed-builder-r4 | 0.546, 0.474 | KKNKNN | 0.907, 0.875 | 0.833, 1.000 | 501 | 0.64 |
| twin-free-collective-r0 | 0.564, 0.434 | KKKKRN | 0.982, 0.995 | 1.000, 0.750 | 631 | 1.02 |
| twin-free-collective-r1 | 0.577, 0.577 | KKKKRK | 0.986, 0.949 | 1.000, 1.000 | 707 | 1.14 |
| twin-free-collective-r4 | 0.450, 0.460 | KKNKNK | 0.986, 0.917 | 1.000, 1.000 | 591 | 0.99 |
| twin-free-rival-r0 | 0.367, 0.614 | KKKKKK | 0.949, 0.902 | 1.000, 1.000 | 655 | 1.34 |
| twin-free-rival-r1 | 0.531, 0.451 | KKNNNN | 0.687, 0.902 | 0.917, 1.000 | 478 | 0.80 |
| twin-free-rival-r4 | 0.551, 0.444 | RKKKNK | 0.875, 1.000 | 1.000, 1.000 | 613 | 0.91 |
| twin-stack-collective-r0 | 0.430, 0.335 | KKKRNN | 1.000, 1.000 | 0.833, 0.833 | 428 | 0.70 |
| twin-stack-collective-r1 | 0.410, 0.539 | KKKNNN | 0.995, 0.995 | 1.000, 1.000 | 381 | 0.56 |
| twin-stack-collective-r4 | 0.420, 0.346 | RKKNNN | 0.986, 0.986 | 1.000, 1.000 | 420 | 0.65 |

K kept, R discarded for a lower score, B discarded at boot, I discarded by the surface rules, N no change.

## Arms

| Arm | Runs | Exam visible, pair mean (each run) | Mean | Exam held-out, pair mean (each run) | Mean | Kept | Lower | Boot | Surface | No change | Builder made an edit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| twin-free-rival | 3 | 0.926, 0.795, 0.938 | 0.886 | 1.000, 0.958, 1.000 | 0.986 | 12 | 1 | 0 | 0 | 5 | 13 of 18 |
| twin-free-collective | 3 | 0.988, 0.967, 0.952 | 0.969 | 0.875, 1.000, 1.000 | 0.958 | 13 | 2 | 0 | 0 | 3 | 15 of 18 |
| twin-stack-collective | 3 | 1.000, 0.995, 0.986 | 0.994 | 0.833, 1.000, 1.000 | 0.944 | 8 | 2 | 0 | 0 | 8 | 7 of 18 |
| solo-pair | 3 | 0.990, 0.965, 0.921 | 0.959 | 0.792, 0.958, 1.000 | 0.917 | 8 | 0 | 0 | 0 | 10 | 8 of 18 |
| twin-fixed-builder | 3 | 0.887, 0.936, 0.891 | 0.905 | 1.000, 1.000, 0.917 | 0.972 | 10 | 2 | 0 | 0 | 6 | 12 of 18 |

Seed harness on the same exam, 12 repeats: visible 0.476, 0.556, 0.457, 0.499, 0.427, 0.584, 0.471, 0.515, 0.492, 0.475, 0.549, 0.510 (mean 0.501), held-out 0.496, 0.849, 0.455, 0.649, 0.432, 0.496, 0.373, 0.514, 0.456, 0.605, 0.389, 0.574 (mean 0.524).

## Contrasts

| Contrast | Visible: difference in means | Exact two-sided p | Held-out: difference | Exact two-sided p |
|---|---|---|---|---|
| twin minus solo | +0.010 | 0.700 | +0.042 | 0.700 |
| live builder minus seed builder | +0.064 | 0.100 | -0.014 | 1.000 |
| stack minus free | +0.025 | 0.200 | -0.014 | 1.000 |
| rival minus collective | -0.083 | 0.100 | +0.028 | 1.000 |

## Gate, turn by turn

Mean over runs of the old harness's score and the candidate's score on the same fresh tasks, for turns where a benchmark ran.

| Arm | t1 | t2 | t3 | t4 | t5 | t6 |
|---|---|---|---|---|---|---|
| twin-free-rival | 0.54 to 0.71 (n=3) | 0.41 to 0.65 (n=3) | 0.69 to 0.99 (n=2) | 0.51 to 0.88 (n=2) | 1.00 to 1.00 (n=1) | 1.00 to 1.00 (n=2) |
| twin-free-collective | 0.55 to 0.88 (n=3) | 0.43 to 0.93 (n=3) | 0.94 to 0.94 (n=2) | 0.95 to 0.99 (n=3) | 0.99 to 0.83 (n=2) | 0.99 to 0.99 (n=2) |
| twin-stack-collective | 0.56 to 0.84 (n=3) | 0.51 to 0.99 (n=3) | 0.80 to 1.00 (n=3) | 1.00 to 0.89 (n=1) | - | - |
| solo-pair | 0.40 to 0.96 (n=3) | 0.39 to 0.89 (n=3) | 0.99 to 1.00 (n=1) | 0.67 to 1.00 (n=1) | - | - |
| twin-fixed-builder | 0.53 to 0.84 (n=3) | 0.48 to 0.92 (n=3) | 0.88 to 0.92 (n=2) | 0.88 to 1.00 (n=2) | 0.82 to 0.99 (n=1) | 0.99 to 0.79 (n=1) |

## Size and economy

| Arm | Pairs whose two final harnesses differ | Mean bytes of a final harness that was ever changed | Model calls used per exam task |
|---|---|---|---|
| twin-free-rival | 3 of 3 | 6822 | 2.92 |
| twin-free-collective | 3 of 3 | 5890 | 3.00 |
| twin-stack-collective | 0 of 3 | 6080 | 2.78 |
| solo-pair | 3 of 3 | 5758 | 2.94 |
| twin-fixed-builder | 3 of 3 | 5130 | 3.00 |

## Builder assay

Each run's final harness of slot A takes one build turn on a fresh seed harness. Gain is the candidate's mean minus the seed's mean on the same 9 fresh tasks, 0 when the candidate was discarded before the benchmark.

| Arm | Assays | Outcomes | Gains | Mean gain |
|---|---|---|---|---|
| twin-free-rival | 3 | KKN | +0.559, +0.436, +0.000 | +0.332 |
| twin-free-collective | 3 | NKK | +0.000, -0.011, +0.092 | +0.027 |
| twin-stack-collective | 3 | KNN | +0.596, +0.000, +0.000 | +0.199 |
| solo-pair | 3 | KKK | +0.498, +0.275, +0.556 | +0.443 |
| twin-fixed-builder | 3 | KKK | +0.515, +0.505, +0.453 | +0.491 |

First-turn gains of seed builders in this block (turn 1 of every run, same definition): +0.474, +0.467, +0.722, +0.382, +0.081, +0.465, +0.221, +0.347, +0.426, +0.465, +0.382, -0.310, +0.455, +0.533, -0.151. Mean +0.331.

## Predictions

| Prediction | Held | Figures |
|---|---|---|
| P1 | yes | twin-free-rival +0.385; twin-free-collective +0.468; twin-stack-collective +0.493; solo-pair +0.458; twin-fixed-builder +0.404 over the seed's 0.501 |
| P2 | yes | twin-free-collective minus solo-pair = +0.010 |
| P3 | yes | twin-free-collective minus twin-fixed-builder = +0.064 |
| P4 | no | stack minus free = +0.025 |
| P5 | yes | rival minus collective: visible -0.083, held-out +0.028 |
| P6 | no | 55 of 90 build turns made an edit |
| P7 | no | 7 of 58 candidates at the gate were discarded, 0 at boot |
| P8 | yes | pooled gain over the seed: visible +0.442, held-out +0.432 |
| P9 | yes | assay mean +0.250 over 12 built harnesses, first-turn mean +0.331 over 15 seed builders, difference -0.080 |

Totals: 15 runs, 8038 model calls, 12.62 dollars, 0 model calls that failed on the referee's side.
