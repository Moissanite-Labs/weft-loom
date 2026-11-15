# Gate-metric calibration: which distance predicts behaviour change?

## Question

The Weft gate accepts a weight update when it stays within a fixed distance of a saved baseline. Does that distance, or any other distance, predict how much the model's behaviour changes? This is the study that [issue 7](https://github.com/Moissanite-Labs/weft-loom/issues/7) asks for.

## Status

`complete`

Both confirmatory runs were made after the preregistration was pushed. Sections marked exploratory were not preregistered.

## Preregistration

[PREREG.md](PREREG.md) was committed and pushed in `a298e8f` at 17:21 UTC on 15 November 2026. The confirmatory runs started after that push. Each results file records the hash of the program that wrote it, and both hashes equal the ones in the preregistration. [THEORY.md](THEORY.md) holds the derivations.

No prediction, threshold, seed or line of the two programs changed after the push. `summarise.py`, `plasm_radius.py`, `null_law.py` and `probe_count_tf.py` were written afterwards. The first only tabulates. The other three are exploratory.

## How to rerun

Needs Python 3.12 with NumPy, and CPU PyTorch for the transformer. Run from this folder inside a weft-loom checkout. `calib.py` imports the E13 record beside it.

```
python3 calib.py --seeds 0 1 2 3 4 5 6 7 8 9 10 11 --out results.json
python3 calib_tf.py --seeds 0 1 2 3 4 5 6 7 8 9 10 11 --out results_tf.json
python3 summarise.py results.json
python3 summarise.py results_tf.json
python3 null_law.py --seeds 0 1 2 3 4 5 6 7 8 9 10 11 --out null_law.json
python3 probe_count_tf.py --seeds 4 5 7 0 1 2 --out probe_count_tf.json
python3 plasm_radius.py --weft /path/to/weft
```

Run on one Apple Silicon Mac, macOS, Python 3.12.15, NumPy 2.5.4, PyTorch 2.15.0. An MLP host takes two to four minutes and a transformer host five to eight on a loaded machine. Results on another machine may differ in the last digits. No second machine was tried.

## Results

### The predictions

A prediction is confirmed if it holds on at least 11 of 12 hosts.

| Prediction | MLP, 12,488 weights | Transformer, 18,839 weights |
|---|---|---|
| H1a The worst direction changes outputs at least 10 times more than a random one | 12 of 12 | 12 of 12 |
| H1b The permutation is far away and changes nothing | 12 of 12 | 12 of 12 |
| H2a The first-order distance matches the change on the probes within 1.1 | 12 of 12 | 12 of 12 |
| H2b It matches the change on held-out inputs within 1.25 | 12 of 12 | **10 of 12** |
| H3a It is blind to moves in the probes' null space | 12 of 12 | 12 of 12 |
| H3b It is off by more than 3 on a large natural move | 12 of 12 | 12 of 12 |
| H4 Change on the probes matches change on held-out inputs within 1.25, for every move made without sight of the probes | 12 of 12 | **9 of 12** |
| H5a A proposer who knows the probes hides at least 10 times more change than they show | 12 of 12 | 12 of 12 |
| H5b That proposer breaks the bar while showing no more change than a benign graft | 12 of 12 | not tested |
| H6a The adversary breaks the bar at a radius 10 times smaller than a random move | 12 of 12 | 12 of 12 |
| H6b One optimiser step is at least as long as the adversary's breaking radius | 12 of 12 | 12 of 12 |
| H6c The benign graft passes at a distance of at least 20 (predicted on at least 10 hosts) | 11 of 12 | not tested |
| H6d A random move breaks the bar inside the smaller shipped radius | 12 of 12 | not tested |
| H7 The certified radius is below the attack radius, and the proved bound is never exceeded | 12 of 12 | not tested |

On the MLP all fourteen predictions are confirmed. On the transformer eight of the ten tested are confirmed and **two are not**: H2b holds on 10 hosts and H4 on 9. Both were predicted to be confirmed.

Every miss comes from one class of move on hosts 4, 5 and 7: the adversary that searches on its own 96 inputs. For that class the change on held-out inputs was between 0.746 and 1.71 times the change on the probes. For every other class it stayed between 0.856 and 1.197 on all 12 hosts. The section on probe count below looks at why.

### How far each kind of move can go (MLP)

Medians over 12 hosts. The native outputs have an RMS of 2.52. "Safe size" is the largest length at which held-out outputs change by at most 0.05. "Breaking radius" is the smallest tested length at which shifted native R2 falls by more than 0.025, on a grid of about half a decade.

| Kind of move | Safe size | Breaking radius |
|---|---|---|
| Adversary inside the ball | 0.0149 | 0.3 |
| Gradient step on native data | 0.0258 | 0.3 |
| Gradient step on the novel skill | 0.0411 | 0.3 |
| Readout flip direction | 0.0802 | 1 |
| Random direction | 0.339 | 3 |
| Inside the null space of the probes | 1.84 | 10 |
| Confined to the least used units | 1.29 | 10 |

Moves at their own length, with the change they cause on held-out native inputs:

| Move | Distance | Change | Fall in native R2 |
|---|---|---|---|
| One optimiser step on the novel skill | 1.01 | 0.463 | 0.0593 |
| Joint training on native and novel skills | 8.74 | 0.266 | 0.0016 |
| Benign E13 graft | 28.1 | 0.21 | 0.017 |
| Hidden-unit permutation | 29.2 | 0 to rounding | 0 |
| Readout flip | 6.6 | 4.17 | 3.63 |

Four things stand out.

- **The ball is the wrong shape by a factor of about 24.** The worst direction changes outputs 3.36 per unit of distance, a random one 0.13. The ratio at radius 0.1 is 25.3 in the median, and between 22.3 and 30.6 on every host.
- **No radius is both safe and useful.** The adversary breaks the retention bar at 0.1 to 0.3. One optimiser step is 1.01 long. A radius small enough to be a guarantee forbids a single training step. The smaller shipped radius, 10, admits random moves that break the bar at 3.
- **Distance does not order the moves that matter.** The benign graft is 28 times farther than one optimiser step and disturbs native behaviour less than half as much. The permutation is farther still and changes nothing.
- **The proved bound is sound and about five times too strict.** No measured change exceeded it on any host. It certifies a radius of 0.00298 for a change of 0.05, where the first-order estimate is 0.0149 and a search first reaches 0.05 at 0.03.

### What predicts held-out change

| Predictor | Result on the MLP |
|---|---|
| Frobenius distance | Off by the anisotropy, and silent on symmetry. Rejected. |
| First-order distance from 256 probes | Within 0.94 to 1.08 of the truth for local moves made without sight of the probes. Predicts 7.31 for the permutation, whose true change is zero, and 1 for the graft, whose true change is 0.21. Zero for moves in its null space, which do change held-out outputs. |
| Measured change on 256 probes | Within 0.93 to 1.08 of the truth for every move made without sight of the probes, at every radius, symmetry and graft included. |
| The same, against a proposer who knows the probes | At radius 1 the held-out change is 23.2 times the change on the probes in the median, and at least 14.7 times on every host. At radius 10 that proposer shows no more change on the probes than the benign graft and drops native R2 by 0.149 in the median. |

### Reading for issue 7

Issue 7 asks whether one distance predicts behaviour change within a stated factor across directions. With the factor set at 1.25 before the run:

- No distance computed from the weights alone passes. This is the issue's fail mark, and its stated consequence follows: the gate needs a behaviour check, not a better norm.
- The behaviour check passes the mark for every move made without sight of the probes.
- It fails against a proposer who has seen them. So the probes must be drawn after the candidate is fixed, or be kept from whoever proposes it.

On the transformer the order of the predictors is the same, and the stated factor is not met. With 96 probes the behaviour check is within 1.25 for every class of move except the independent adversary, where it is within 1.71. The first-order distance has the same weakness, because it is built from the same 96 probes.

So for this model the answer to issue 7 is the same branch with a caveat on probe count. That caveat was not predicted.

### How far each kind of move can go (transformer)

Medians over 12 hosts. The centred logits have an RMS of 4.02. The drop score is held-out accuracy, with the bar at 0.025.

| Kind of move | Safe size | Breaking radius |
|---|---|---|
| Adversary inside the ball | 0.00234 | 0.1 |
| Gradient step on native data | 0.00421 | 0.2 |
| Gradient step on the novel skill | 0.0061 | 0.3 |
| Random direction | 0.0592 | 3 |
| Readout flip direction | 0.0928 | never broken on the grid |
| Inside the null space of the probes | 0.149 | never broken on the grid |

| Move | Distance | Change | Fall in accuracy |
|---|---|---|---|
| One optimiser step on the novel skill | 0.137 | 0.641 | 0 |
| Joint training on native and novel skills | 6.66 | 2.92 | 0 |
| Hidden-unit permutation | 17.1 | 0 to rounding | 0 |

The same picture holds. The worst direction changes the logits 28.3 per unit of distance, a random one 0.783, a ratio of 37.4. The adversary breaks the accuracy bar at 0.1 on every host, and one optimiser step is 0.137 long.

A proposer who knows the probes hides the change far better here than on the MLP: at radius 0.01 the held-out change is 459 times the change on the probes in the median, and at least 50.3 times on every host.

### The linear cell (exploratory)

The Plasm cell of the weft runtime is one square matrix, `out = x W`. For a linear map the gate's bound is exact: for every input, `||x dW|| <= ||x|| ||dW||`, and a move exists that reaches it. `plasm_radius.py` evaluates this on the stimulus and weights the Plasm cycle builds, and constructs the worst move to check that the bound is reached.

- The cell's output RMS is 0.199. The worst move changes it by 0.0783 per unit of distance, a random move by 0.0154.
- At the shipped radius of 120 the worst case is 47 times the cell's own output.
- At the largest drift Paper 1 reports, 0.463, the worst case is 18 percent of the output.
- A radius of 0.127 keeps the worst case under 5 percent of the output, and 0.0254 keeps it under 1 percent.

This gives weft issue 74 a rule for a linear cell: `R = tolerance * output RMS * sqrt(n d) / smax(X)`, with `X` the `n` stimuli of width `d` and `smax` its largest singular value.

### How quiet is an edit in the null space? (exploratory)

THEORY.md section 6 says an edit inside the null space of a keep set changes the keep inputs only at second order, and leaks at first order onto inputs it did not see. `null_law.py` measures the leak on the 12 MLP hosts as the keep set grows. The leak is the held-out change of a random null-space move, as a share of the change a random move of the same length causes.

| Keep inputs | Silent directions left, of 12,488 | Leak onto held-out inputs |
|---|---|---|
| 16 | 12,360 | 0.551 |
| 32 | 12,232 | 0.45 |
| 64 | 11,976 | 0.349 |
| 128 | 11,464 | 0.268 |
| 256 | 10,440 | 0.188 |
| 512 | 8,392 | 0.124 |

Each doubling of the keep set cuts the leak by between a fifth and a third, and every keep input uses up 8 silent directions. At 1,561 keep inputs no silent direction is left. So an edit in the null space is two to eight times quieter than a random edit on inputs nobody listed, never silent, and the quieter it is made the less room is left to edit.

This is the number behind both readings of the null space in the Weft records: safe for the listed inputs, and a hiding place on the others.

### Why the probe check missed its mark on three transformer hosts (exploratory)

`probe_count_tf.py` rebuilds six hosts, finds the same kind of adversarial move at the local radius, and redraws the probe set 200 times at each size. Each cell is the 2.5th to 97.5th percentile of the ratio between the change on the remaining inputs and the change on the probes.

| Host | Share of the squared change on the 5 percent of inputs changed most | 24 probes | 96 probes | 384 probes |
|---|---|---|---|---|
| 4 | 0.65 | 0.59 to 2.74 | 0.71 to 1.53 | 0.80 to 1.23 |
| 5 | 0.88 | 0.32 to 3.31 | 0.44 to 2.44 | 0.49 to 1.99 |
| 7 | 0.56 | 0.57 to 2.08 | 0.75 to 1.46 | 0.83 to 1.21 |
| 0 | 0.36 | 0.75 to 1.54 | 0.85 to 1.23 | 0.87 to 1.13 |
| 1 | 0.43 | 0.68 to 1.55 | 0.81 to 1.26 | 0.88 to 1.17 |
| 2 | 0.50 | 0.58 to 1.75 | 0.77 to 1.34 | 0.84 to 1.19 |

The three hosts that missed are the three where the adversary's move is most concentrated. More than half of its squared change falls on one input in twenty. A small probe set either holds some of those inputs or does not, so its reading swings. More probes narrow the swing. On host 5, where 88 percent of the change sits on 5 percent of the inputs, 384 probes out of 962 inputs still leave a factor of two.

This is Proposition 2 of the theory note seen from the other side. A probe check bounds the share of inputs that change. It does not bound the size of a change that falls on a few. The more a move concentrates its effect, the more probes it takes to see it.

A trigger that fires on a sliver of the input space is the limiting case, and the admission test in the recheck record shows it: 48 of 48 such grafts were admitted.

## Limits

- Two small models on synthetic tasks, one probe-set size each. Nothing here was run on a pretrained model.
- The adversaries are gradient searches. A breaking radius is an upper bound on the true one.
- The grid of radii is coarse, about half a decade. H6a and H6b hold at that resolution.
- The proved bound is evaluated in double precision, not interval arithmetic, and covers the MLP only.
- The transformer is trained on its whole finite input space. "Held-out" there means unseen by the predictor.
- Two predictions failed on the transformer. The explanation offered for them is exploratory and was found after the run.
- The linear-cell numbers use the stimulus the Plasm cycle builds. Another stimulus gives another radius.
- One machine. The record has not been rerun elsewhere.

## Disclosure

Written and run by an AI agent session with human oversight. The E13 organism, task world, trainer and splice are imported unchanged from the E13 record.

> Automated posting by agentic team with human oversight.
