# Recheck of the Weft thread evaluation, 2026-11-15

## Question

Do the results in the thread record `experiments/weft-threads-2026-11-15`, and in the open work around it, hold when someone else re-runs them and adds the controls they lack? And with that done, where does Weft stand?

## Status

`exploratory`

## Preregistration

Not preregistered, with two exceptions. The admission rule was frozen, with the hashes of the files its thresholds came from, before any new graft was built. The calibration study is its own record, `experiments/gate-metric-calibration-2026-11-15`, and was preregistered.

## What is here

| File or folder | What it holds |
|---|---|
| [EVALUATION.md](EVALUATION.md) | Where Weft stands: new ground, what others would value, threads to pull, and how the threads tie together |
| [review-meta.md](review-meta.md) | What 93 review findings and 154 audited sentences have in common |
| `repro/` | A rerun of every probe of the thread record, with a comparer |
| `admission/` | The two-check admission rule, frozen, on 48 new host and donor pairs and nine harm classes |
| `runtime/` | The weft test commands, a differential test of the gate in three languages, a sentence audit of the README and papers, and a check of the claims register |
| `colony/` | The colony laws recomputed from the raw logs, with exact tests and a power calculation |
| `prs/` | Controls and tamper tests run against open weft pull requests 180, 181, 182, 201 and 206 |
| `tf/` | The transformer splice on fresh seeds, with controls, and an attempt at an attention graft |
| `meta/` | The list of findings and the program that counts them |
| `claims/` | A ledger that checks sentences in these notes against the data files |
| `issues/` | The body of each issue filed from this record |

## Results

### The thread record reproduces

Nine result files were regenerated and compared with the committed ones: eight are identical and one, the E13 certificate, differs by at most 9.67e-07. `repro/compare.out` has the lines. A sentence-by-sentence check of the record's README, workspace note and four issue bodies found no number that disagrees with its file.

What the check did find is in `meta/findings.json` under the source `repro`. The main ones:

- "Wire-only" removes only the readout refit. The splice still uses the keep and synthesis inputs, the true skill index and a hand-set shunt. Arm A3 moved from 0.5386 to 0.4626, so the refit was not a no-op everywhere.
- The admission thresholds were set on the same 12 benign grafts they were then said to accept.
- "The two checks cover every harm class" was never run as one rule.
- The transformer bar was reported on the third variant, after two that failed.

### The admission rule on new data

The rule admits a graft when held-out native drift is at most 0.533415 and donor agreement is at most 0.6693. Both thresholds were frozen from the committed files. 48 new pairs, each in its own task world.

| Class | Grafts | Admitted | Fail the joint bar |
|---|---|---|---|
| Benign | 48 | 48 | 1 |
| Three harm classes of the earlier study | 144 | 0 | 144 |
| Smallest sabotage that fails the bar, two kinds | 94 | 0 | 94 |
| Packet for the wrong skill | 48 | 0 | 48 |
| Trigger written into the host | 48 | 48 | 3 |
| Honest packet from a weak donor | 48 | 37 | 40 |

- On the classes it was designed for, the rule holds on new data: no benign graft rejected, no harmful graft admitted.
- The drift check never rejected a graft that the agreement check had not already rejected. On this set the rule is the agreement check alone.
- Donor agreement measures faithfulness to the donor, not quality. Of the 40 weak-donor grafts that fail the joint bar, 32 were admitted.
- A trigger that fires outside the range the probes reach was admitted 48 times out of 48. The probes cannot see it.
- The weight-distance gate admits none of the 478 grafts at radius 10, benign ones included. At radius 120 it admits 464, among them 317 of the 331 that fail the joint bar.

### The runtime

- 27 test and check commands were run on weft main at `aada4c6`. Three failures are real: one Plasm test that only runs on Apple GPUs, and the bundle build with its verifier, because the pinned commit is not in the history. Two more commands could not run for want of tools on this machine.
- The gate in Python, C and JavaScript was run on 20,992 inputs. The Python list path and the JavaScript gate agree on every accept decision. The C gate differs on 2, in the safe direction. The Python tensor path accepts moves just over the radius, as `runtime/tensor_path_repro.out` shows with exact arithmetic: 199 of 199 constructed cases.
- The C gate debits the caller's budget on three reject paths, as weft issue 210 says. The shared test vectors expect exactly that, so it is a choice of specification, not an accident.
- The sentence audit and the register check are summarised in `review-meta.md`.

### The colony laws

Recomputed from the raw logs by `colony/colony_stats.py`, and the first count again by `colony/recount_first_choice.py`, written apart.

- Price display: 26 of 32 cells chose the cheapest model at their first act when prices were shown, and 0 of 32 when they were hidden. Every shown run is above every hidden run.
- Hidden prices cost 2.95 and 2.42 times the energy in the two pairs of arms. Between 2.0 and 2.9 remains under every treatment of the runs that the no-credit rule cut short.
- Score display: the effect on reach is +0.543 with all four tasks and -0.019 without the fibmod task.
- Across the three colony records, 129 guesses were written down. 73 held, 44 missed and 12 could not be judged.
- A replication able to see a score effect of 0.10 needs about 64 runs per arm, or 26 without fibmod. The current blocks have 3 or 4.

### Open pull requests

Controls were added to two benchmarks and removed their advantage. The lead re-ran two of the E15 arms.

- E15 dual morphogenesis (pull requests 180 and 206, on main): the numbers reproduce. An arm that gets the same information through a plain threshold also passes 12 of 12. With the teacher rows placed at random the favoured arm passes 0 of 12.
- E11 rerun (pull request 201): reproduces as the author reports, 3 of 6 bars met. An arm that transfers nothing and only fits the new output row matches the plasmid arm between independently trained networks: 0.705 against 0.703 on 20 fresh seeds. With the true alignment handed over, the plasmid arm is higher, 0.806 against 0.736.
- Probe refresh (pull request 181): it vetoes the planted attacks, and also every ordinary update tried. Its challenge is computable by the proposer, who can search for a passing input.
- Routing and mitosis gate (pull request 182): the routing is correct on valid input. A receptor id equal to the sink index yields a wrong flow marked as verified.

### The transformer splice

The thread record reports a skill spliced into a 272,384-parameter transformer with all three skills at 1.0 "on 2 of 2 seeds", and says a reversal skill cannot be spliced until an attention graft exists. `tf/` reruns it on 20 fresh seeds and tests the second statement directly. Seed 3 was used to settle the graft's training length, so it is not a clean test for the graft.

| Arm, 20 fresh seeds | Pass |
|---|---|
| The record's packet, spliced into dormant units | 13 of 20 |
| The same packet as an outside adapter | 17 of 20 |
| A packet trained on a donor's outputs with no true labels, spliced | 17 of 20 |
| The record's packet in random units | 12 of 20 |
| A packet trained without the term that preserves native skills | 0 of 20 |
| An outside router that switches on the task token | 20 of 20 |

- The "2 of 2" result is a pass rate of about two in three. The exact 95 percent interval for 13 of 20 runs from 0.41 to 0.85.
- Dormant units are not clearly better than random ones here: 13 against 12.
- Training the packet on a donor, which the record lists as a limit it did not remove, changes nothing.
- The weight-distance gate rejects all 20 splices at radius 10 and accepts all 20 at radius 120, whether they work or not.

The statement about attention is wrong as written. With all attention weights frozen, retraining the position-wise layers alone reaches a reversal accuracy of 1.0 on 8 of 8 seeds. A packet of 16,576 weights at the first layer's position-wise block does it on 8 of 8 seeds, with native skills intact. The same packet at the last block fails on 8 of 8.

The first-layer packet rewrites the position codes that the frozen second-layer attention reads, and the attention then looks at the mirrored position.

An attention graft of one head, 16,480 weights, was built as the record proposed. Written over a head whose removal leaves native skills unchanged, it learns the reversal on 5 of 8 seeds. As an added head it does so on 4 of 8 in the second layer and 3 of 8 in the first. Native skills stay at 1.0 in all 32 runs. Trained with the task token hidden, the graft fires on every context and native accuracy falls.

The lead re-ran the frozen-attention test on two seeds the worker did not use. Both reached a reversal accuracy of 1.0.

### Taken together

[EVALUATION.md](EVALUATION.md) gives the reading, and [review-meta.md](review-meta.md) the pattern in the findings.

## How to rerun

From the root of a weft-loom checkout. `PY` is a Python 3.12 with NumPy and SciPy, and PyTorch for the transformer parts. `W` is a checkout of the weft repository.

```
PYTHON=$PY WEFT_CHECKOUT=$W bash experiments/weft-threads-recheck-2026-11-15/repro/run_all.sh
python3 experiments/weft-threads-recheck-2026-11-15/repro/compare.py
NPROC=4 $PY experiments/weft-threads-recheck-2026-11-15/admission/admission_oos.py
$PY -I experiments/weft-threads-recheck-2026-11-15/colony/colony_stats.py --weft $W
$PY -I experiments/weft-threads-recheck-2026-11-15/colony/power_sim.py
python3 experiments/weft-threads-recheck-2026-11-15/colony/recount_first_choice.py
WEFT_CHECKOUT=$W PYTHON=$PY bash experiments/weft-threads-recheck-2026-11-15/runtime/run_diff.sh
$PY experiments/weft-threads-recheck-2026-11-15/runtime/tensor_path_repro.py --weft $W
python3 experiments/weft-threads-recheck-2026-11-15/meta/classify.py
python3 experiments/weft-threads-recheck-2026-11-15/claims/check_claims.py
```

The scripts in `prs/ctrl/` take a worktree of the pull request head as their argument. The heads are `f71467b` (180), `7d1ea99` (181), `df40620` (182), `fb5d19a` (201) and `16e1a18` (206), fetched with `git fetch origin pull/N/head`.

Everything ran on one Apple Silicon Mac, macOS, Python 3.12.15, NumPy 2.5.4, PyTorch 2.15.0. After packaging, each program was run again from this folder and gave the same output as before, timing fields aside.

## Checked a second time by the lead

Most of the reruns were made by agent workers. These were then checked again by the lead, with a separate program or by hand:

- The tensor-path defect, with exact rational arithmetic.
- The Plasm test that fails on an Apple GPU.
- Six of the stale register rows.
- The colony first-choice counts.
- Two arms of the E15 control, and the E11 control on all 25 seeds.
- The nine result files of the reproduction, through `repro/compare.py`.
- The frozen-attention test of the transformer, on two new seeds.

The rest stands on one run by a worker and one rerun after packaging.

## Limits

- Toy tasks throughout. Nothing was run on a pretrained model.
- One machine. No part was rerun on Linux.
- The harm classes added to the admission test were designed after reading the rule.
- The colony analysis uses the committed logs. No new colony run was made, so nothing here replicates the laws.
- The controls on open pull requests reuse the authors' seeds, apart from 20 fresh seeds for E11.
- The kinds and directions in `meta/findings.json` were assigned by one reader.

## Disclosure

Produced by an AI agent session with human oversight. Subagents ran the reproduction, the admission test, the runtime checks, the colony statistics, the pull-request controls and the transformer work, each from a written brief. The lead wrote the notes, the ledger and the calibration study.

> Automated posting by agentic team with human oversight.
