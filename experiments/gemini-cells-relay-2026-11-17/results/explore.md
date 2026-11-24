# Descriptions written after the runs were seen (explore.py)

Nothing in this file was preregistered.

## Where the gain came from

For every candidate that reached the paired benchmark: the old harness's score and the candidate's, on the same 9 fresh tasks. "First" is the first such candidate for a slot in a run, "later" is every one after it.

| Arm | First: candidates | old mean | new mean | Later: candidates | old mean | new mean |
|---|---|---|---|---|---|---|
| twin-free-rival | 8 | 0.470 | 0.756 | 10 | 0.814 | 0.971 |
| twin-free-collective | 8 | 0.476 | 0.912 | 10 | 0.968 | 0.938 |
| twin-stack-collective | 6 | 0.535 | 0.913 | 4 | 0.851 | 0.972 |
| solo-pair | 8 | 0.402 | 0.912 | 6 | 0.887 | 0.949 |
| twin-fixed-builder | 8 | 0.508 | 0.890 | 8 | 0.913 | 0.938 |
| all arms | 38 | 0.475 | 0.875 | 38 | 0.891 | 0.952 |

## What builders did at a high score

Build turns where the scoreboard showed the target's harness at 0.95 or more, and what the builder did.

| Arm | Such turns | Made an edit | Edit kept | Edit discarded | No change | Mean model calls used |
|---|---|---|---|---|---|---|
| twin-free-rival | 7 | 5 | 5 | 0 | 2 | 13.0 |
| twin-free-collective | 9 | 5 | 4 | 1 | 4 | 13.4 |
| twin-stack-collective | 11 | 1 | 0 | 1 | 8 | 11.1 |
| solo-pair | 9 | 3 | 3 | 0 | 6 | 6.8 |
| twin-fixed-builder | 10 | 3 | 3 | 0 | 7 | 7.7 |

## Cost by arm

| Arm | Runs | Dollars per run | Model calls per run | Build calls per turn | Minutes per run |
|---|---|---|---|---|---|
| twin-free-rival | 4 | 1.00 | 592 | 13.9 | 29 |
| twin-free-collective | 4 | 0.97 | 607 | 13.8 | 26 |
| twin-stack-collective | 3 | 0.64 | 410 | 11.9 | 18 |
| solo-pair | 4 | 0.79 | 530 | 10.9 | 20 |
| twin-fixed-builder | 4 | 0.81 | 564 | 11.4 | 21 |

## Every fault-free run

The planned analysis reads only replicates complete in all five arms. This table adds the runs it leaves out.

| Arm | Runs | Exam visible, pair mean (each run) | Mean | Exam held-out, pair mean (each run) | Mean |
|---|---|---|---|---|---|
| twin-free-rival | 4 | 0.926, 0.795, 0.985, 0.938 | 0.911 | 1.000, 0.958, 1.000, 1.000 | 0.990 |
| twin-free-collective | 4 | 0.988, 0.967, 0.965, 0.952 | 0.968 | 0.875, 1.000, 1.000, 1.000 | 0.969 |
| twin-stack-collective | 3 | 1.000, 0.995, 0.986 | 0.994 | 0.833, 1.000, 1.000 | 0.944 |
| solo-pair | 4 | 0.990, 0.965, 0.876, 0.921 | 0.938 | 0.792, 0.958, 0.958, 1.000 | 0.927 |
| twin-fixed-builder | 4 | 0.887, 0.936, 0.907, 0.891 | 0.906 | 1.000, 1.000, 1.000, 0.917 | 0.979 |

## Kept candidates with and without an edit

| Arm | Kept | of which the builder had edited | of which a plain copy of the builder's harness |
|---|---|---|---|
| twin-free-rival | 17 | 17 | 0 |
| twin-free-collective | 15 | 15 | 0 |
| twin-stack-collective | 8 | 5 | 3 |
| solo-pair | 14 | 14 | 0 |
| twin-fixed-builder | 13 | 13 | 0 |

## The final harnesses with one model call per task

Each final harness sat the same exam again with 1 model call per task in place of 3. One sitting each.

| Arm | Final harnesses measured | Visible at 1 call (each) | Mean | Held-out at 1 call, mean | Visible at 3 calls, mean |
|---|---|---|---|---|---|
| twin-free-rival | 6 | 0.82, 0.97, 0.17, 0.83, 0.94, 0.17 | 0.649 | 0.599 | 0.902 |
| twin-free-collective | 6 | 0.17, 0.17, 0.17, 0.17, 0.94, 0.17 | 0.295 | 0.131 | 0.973 |
| twin-stack-collective | 4 | 0.79, 0.79, 0.82, 0.82 | 0.805 | 0.875 | 0.997 |
| solo-pair | 6 | 0.96, 0.77, 0.17, 0.90, 0.17, 0.31 | 0.545 | 0.592 | 0.944 |
| twin-fixed-builder | 6 | 0.17, 0.17, 0.17, 0.17, 0.17, 0.90 | 0.288 | 0.159 | 0.910 |

The seed harness with 1 call: visible 0.175, held-out 0.022.

## The builder assay over every fault-free run

Gain is the candidate's mean minus the seed's on the same 9 fresh tasks, 0 when nothing reached the benchmark.

| Arm | Assays | Gains | Mean gain | Turns with no change |
|---|---|---|---|---|
| twin-free-rival | 4 | +0.000, +0.559, +0.058, +0.436 | +0.263 | 1 |
| twin-free-collective | 4 | -0.011, +0.092, +0.000, +0.000 | +0.020 | 2 |
| twin-stack-collective | 3 | +0.596, +0.000, +0.000 | +0.199 | 2 |
| solo-pair | 4 | +0.498, +0.275, +0.639, +0.556 | +0.492 | 0 |
| twin-fixed-builder | 4 | +0.505, +0.453, +0.423, +0.515 | +0.474 | 0 |

First-turn gains of seed builders over the same 19 runs: mean +0.364.
