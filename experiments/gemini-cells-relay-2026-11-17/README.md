# Gemini-cells relay, 2026-11-17

## Question

Weft-loom pull request 27 proposes twin cells that take turns editing each other's harness. Three questions, fixed in the preregistration:

1. Does that end with better harnesses than two cells that each edit their own harness under the same referee?
2. Does a cell that has been given a better harness build better than a cell left in the seed?
3. Among the three arrangements the owner proposed, does any end ahead?

The proposal, its variations and an exact model of its scoring rules are in [`notes/gemini-cells.md`](../../notes/gemini-cells.md).

## Status

`pilot`

## Preregistration

[PREREG.md](PREREG.md), committed and pushed at 2026-11-17T05:27:48Z as commit `0ddfde4`, with the hash of every frozen file. The first relay run started at 05:28:07Z. The calibration came before the plan and is described in it.

## What is here

| Path | What it holds |
|---|---|
| [PREREG.md](PREREG.md) | Design, calibration, measures, nine predictions with pass marks, spend cap, frozen file hashes |
| `seed/` | The seed harness every cell starts from: a loop, a prompt and two tool files. The only code a cell may change |
| `referee/sandbox.py` | Runs cell code with no network, no credentials and one writable folder |
| `referee/brain.py`, `referee/cellapi.py` | The capped, logged line from a cell to its model, and the spend ledger |
| `referee/bench.py` | Episodes, benchmarks, harness snapshots stored by hash, and build turns |
| `referee/relay.py` | The turn loop, the gate, the five arms and the brief a builder reads |
| `referee/tasks/` | Five families of generated tasks with hidden checkers, and their self-test |
| `run.py`, `analyze.py`, `pack.py` | Commands for calibration, runs and assays; the tables; the packing of results |
| `calibration/ref-harness/` | A harness written by the lead, used only to check that the benchmark tells a better harness from the seed |
| `tests/` | Offline tests of the relay with a scripted model (13 when the pilot ran; more were added for block 2, see below), and the sandbox self-test (26 of 26 checks in `results/sandbox_selftest.out`) |
| `results/tables.md`, `results/summary.json` | Written by `analyze.py` from the run logs. Every figure in the tables below is copied from `tables.md` |
| `results/runs/<run>/log.jsonl` | One row per baseline, turn and exam, with every harness named by the hash of its tree |
| `results/runs/<run>/artifacts.tar.gz` | The build traces of the run and every harness snapshot it produced |
| `results/assay-*.jsonl` | The builder assays |
| `results/explore.md`, `explore.py` | Descriptions written after the runs were seen. Not preregistered |
| `results/kexam-1.jsonl` | The final harnesses of replicates 0 to 2 on the exam with one model call per task |
| `results/changes/` | What builders changed, edit by edit: mechanical counts and one reader's coding |
| `results/faulted/` | Logs of the six runs set aside for a referee fault, and one exam re-sit |
| `second_count/` | A second agent session's recount and its check of the logs against each arm's rules |
| `forgery_check.py`, `results/forgery_check.out` | A scan of every snapshot and build trace for signs of a forged score |
| `check_numbers.py`, `results/check_numbers.out` | Checks that every decimal figure in this README and in the note's sections on the pilot and the model traces to an output file |
| `results/seed_exam.json`, `ref_exam.json`, `gate_noise.json`, `calibration.jsonl` | The calibration |
| `results/warm/log.jsonl` | The excluded warm run |
| `results/MANIFEST.sha256` | SHA-256 of every packed log, archive and assay file |

## How to rerun

The offline checks need root on Linux and no model:

```
cd experiments/gemini-cells-relay-2026-11-17
python3 -m unittest tests.test_offline
python3 tests/sandbox_selftest.py
python3 referee/tasks/selftest.py
```

The tables can be rebuilt from the committed logs with any Python 3:

```
python3 analyze.py
python3 explore.py
python3 second_count/recount_final.py
python3 forgery_check.py
python3 check_numbers.py
python3 block2/analyze_a.py 'block2/partA/assay2-partA-*.jsonl'
python3 block2/explore_a.py 'block2/partA/assay2-partA-*.jsonl'
python3 block2/verify_partA.py --ledger block2/partA/spend.json 'block2/partA/assay2-partA-*.jsonl'
```

The runs were live calls to a hosted model and are not seeded, so running them again gives a new sample and costs money. They need root on Linux and the `claude` command line tool signed in. `R` is an empty folder outside the repository:

```
python3 run.py exam --root R --harness seed --label seed --repeats 12
python3 run.py aa --root R --n 6
python3 run.py block --root R --reps 4 --jobs 5
python3 run.py assay --root R
python3 pack.py R
```

Block 2's part A refuses to start without an approval file for its own run folder (`block2/PLAN.md`, "Approval"): `python3 run.py assay2 --root R2 --tag partA --approval APPROVAL.json`.

Everything ran in one Linux container (kernel 6.18, 4 cores, Python 3.13.18, `claude` 2.1.326) on 2026-11-17.

## Deviations from the plan

1. **A backend outage cost a replicate and a run.** From about 07:00 to 09:00 UTC the account behind the model was out of allowance, and calls were refused with "You've hit your 5-hour limit". Replicate 3 started inside that window: every model call of its five runs failed and none cost anything. Its logs are in `results/faulted/`. A replacement, replicate 4, ran from 09:20 to 09:49 UTC with no failed call.
2. **`twin-stack-collective-r2` is excluded as a referee fault.** The outage began during it. Two of its gate episodes, one in turn 3 and one in turn 4, were ended by the 300-second limit with a score of 0 and no failed call on record, and 13 calls of its exam failed. The turn 3 candidate was kept with 0.652 against the old harness's 0.667, inside the margin, when one of the old harness's nine episodes had been zeroed that way. So that decision cannot be trusted. Its final harness sat the exam again after the outage (`exam_resit.jsonl`, 0.743 over all families). The re-sit is kept and not used, because the fault reached the turns and not only the exam.
3. **So the planned tables read replicates 0, 1 and 4.** The plan analyses only replicates complete in all five arms, and with that run excluded replicate 2 is not. Its other four runs are fault-free. `results/explore.md` shows every fault-free run beside the planned tables.
4. **Three frozen files changed after replicates 0 to 2,** none in a way that alters what a cell sees or how anything is scored. Commit `ac808c4` has the diff. Before replicate 4, `referee/brain.py` was changed to retry a failed call for about seven minutes, not one, and `run.py` got a shorter scratch path for the assay and a `resit` command. During replicate 4, and so used only by the assays, `brain.py` and `bench.py` were changed to wait and rerun an episode that met a usage-limit refusal. The hashes in the plan are those of commit `0ddfde4`, which replicates 0 to 2 ran on.
5. **The assays' first launch died before any model call,** on a socket path longer than the system allows. The path was shortened and they ran after replicate 4.
6. **Added after the runs were seen, and not planned:** `explore.py`, the exam with one call per task, the second count in `second_count/`, and the reading of what builders changed in `results/changes/`.

## Results

`results/tables.md` holds every table of the planned analysis. The figures here are copied from it.

### The arms

Exam scores are from 0 to 1. Each run gives one figure, the mean of its two final harnesses. The seed harness scores 0.501 on the visible families and 0.524 on the held-out ones, over 12 sittings.

| Arm | Runs | Exam visible, pair mean (each run) | Mean | Exam held-out, pair mean (each run) | Mean | Kept | Lower | Boot | Surface | No change | Builder made an edit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| twin-free-rival | 3 | 0.926, 0.795, 0.938 | 0.886 | 1.000, 0.958, 1.000 | 0.986 | 12 | 1 | 0 | 0 | 5 | 13 of 18 |
| twin-free-collective | 3 | 0.988, 0.967, 0.952 | 0.969 | 0.875, 1.000, 1.000 | 0.958 | 13 | 2 | 0 | 0 | 3 | 15 of 18 |
| twin-stack-collective | 3 | 1.000, 0.995, 0.986 | 0.994 | 0.833, 1.000, 1.000 | 0.944 | 8 | 2 | 0 | 0 | 8 | 7 of 18 |
| solo-pair | 3 | 0.990, 0.965, 0.921 | 0.959 | 0.792, 0.958, 1.000 | 0.917 | 8 | 0 | 0 | 0 | 10 | 8 of 18 |
| twin-fixed-builder | 3 | 0.887, 0.936, 0.891 | 0.905 | 1.000, 1.000, 0.917 | 0.972 | 10 | 2 | 0 | 0 | 6 | 12 of 18 |

### The predictions

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

Judged as written, six of nine held and three did not.

- **P1.** Every arm ended at least 0.385 above the seed on the visible families.
- **P2 and P3.** The twins under one score ended 0.010 above the solo pairs and 0.064 above the twins whose builder never left the seed. Both are inside the 0.10 mark. The second is also the one contrast where every run of one arm is above every run of the other, which with three runs an arm is the smallest p an exact test can give, 0.100.
- **P4.** Stack ended 0.025 above free, under the 0.03 mark. Both arms are at the top of the scale.
- **P5.** Rival ended 0.083 below collective on the visible families, below it in every replicate, and 0.028 above on the held-out ones.
- **P6.** Builders made an edit in 55 of 90 build turns, 61 percent against the 75 expected.
- **P7.** The gate discarded 7 of 58 candidates, 12 percent, all for a lower score. None failed to boot, so the second half of the prediction failed. The excluded warm run had one that did not boot.
- **P8.** The gain carried to families no builder saw: +0.432 against +0.442.
- **P9.** The final harnesses of the four arms other than the seed-builder arm gained +0.250 on average when given one build turn on a fresh seed, against +0.331 for seed builders at turn 1 of the same runs. The difference, -0.080, is inside the mark. The arms differ a great deal inside that average, as the assay table shows.

### Contrasts

| Contrast | Visible: difference in means | Exact two-sided p | Held-out: difference | Exact two-sided p |
|---|---|---|---|---|
| twin minus solo | +0.010 | 0.700 | +0.042 | 0.700 |
| live builder minus seed builder | +0.064 | 0.100 | -0.014 | 1.000 |
| stack minus free | +0.025 | 0.200 | -0.014 | 1.000 |
| rival minus collective | -0.083 | 0.100 | +0.028 | 1.000 |

With three runs an arm the smallest two-sided exact p is 0.100.

### Builder assay

Each run's final harness of slot A takes one build turn on a fresh seed harness, with the brief of the arm with one score and free lineages. Gain is the candidate's mean minus the seed's mean on the same 9 fresh tasks, and 0 when nothing reached the benchmark.

| Arm | Assays | Outcomes | Gains | Mean gain |
|---|---|---|---|---|
| twin-free-rival | 3 | KKN | +0.559, +0.436, +0.000 | +0.332 |
| twin-free-collective | 3 | NKK | +0.000, -0.011, +0.092 | +0.027 |
| twin-stack-collective | 3 | KNN | +0.596, +0.000, +0.000 | +0.199 |
| solo-pair | 3 | KKK | +0.498, +0.275, +0.556 | +0.443 |
| twin-fixed-builder | 3 | KKK | +0.515, +0.505, +0.453 | +0.491 |

First-turn gains of seed builders in this block (turn 1 of every run, same definition): +0.474, +0.467, +0.722, +0.382, +0.081, +0.465, +0.221, +0.347, +0.426, +0.465, +0.382, -0.310, +0.455, +0.533, -0.151. Mean +0.331.

### After the runs were seen

Not preregistered. `results/explore.md` has the tables.

- **Where the gain came from.** Over all 19 fault-free runs, the first candidate of each slot to reach the gate moved the score on the same fresh tasks from 0.475 to 0.875 (38 candidates). Every later candidate together moved it from 0.891 to 0.952 (38 candidates).
- **At a high score.** When the scoreboard showed the target at 0.95 or more, builders made an edit in 17 of 46 turns: 5 of 7 under rival scoring, 5 of 9 under one score with free lineages, 1 of 11 with stack, 3 of 9 solo and 3 of 10 with a seed builder.
- **Every fault-free run.** Adding the four fault-free runs of replicate 2 changes no reading. Visible means: rival 0.911, free 0.968, stack 0.994 (3 runs), solo 0.938, seed builder 0.906. Every run of the free arm (lowest 0.952) is above every run of the seed-builder arm (highest 0.936), four against four.
- **The assay over every fault-free run.** Mean gains: rival +0.263, free +0.020, stack +0.199 (3 runs), solo +0.492, seed builder +0.474. Every assay of a free-arm harness (highest +0.092) is below every assay of a solo harness (lowest +0.275) and of a seed-builder harness (lowest +0.423). Seed builders at turn 1 of the same 19 runs gained +0.364. So the harnesses that the twins under one score built for each other were the weakest builders measured, and the harnesses from the two control arms built as well as a seed cell or better. The comparison by arm was not planned. *Added 2026-11-24:* measured again with both slots and six fresh assays a run, as preregistered in part A of block 2, this gap did not hold: free +0.285 against solo +0.372, exact p 0.4286. See "Block 2" below.
- **One call per task.** The final harnesses of replicates 0 to 2 sat the exam again with 1 model call in place of 3, one sitting each. The scores split in two. Of the 28 final harnesses measured, 14 cannot finish in one call and score 0.17, which is what doing nothing scores, one scores 0.31, and 13 score 0.77 to 0.97. Those 13 are 4 of 6 from the rival arm, 1 of 6 from the arm with one score and free lineages, 4 of 4 from stack, 3 of 6 solo and 1 of 6 from the seed-builder arm. The seed scores 0.175. So fewer calls do not give a block room for long: the best harnesses the pilot's cells built already score above 0.9 with one.

### What builders changed

A second agent session read all 58 edits and all 28 turns without an edit in replicates 0 to 2, which include the excluded run, since its edits are still what a builder wrote. The counts of files, lines and keywords are mechanical (`results/changes/changes.py`). The kinds are one reader's judgement, with a quote kept for each (`changes_coded.jsonl`, `noops.jsonl`, `summary.md`).

- **No tool was ever added.** Every candidate keeps the seed's four files. 49 of 58 edits changed the loop in a general way: show the notes first, raise the output cap, trim the prompt to fit.
- **Advice tied to the benchmark's own families** appears in 12 of 13 rival edits, 8 of 14 under one score with free lineages, 6 of 7 with stack, 5 of 11 solo and 4 of 13 with a seed builder. A family is named in 6 of 13 rival edits and in 1 of 45 others. Two rival runs carry most of this.
- **No sabotage was found.** No rival builder removed a tool or lowered an existing cap. 22 of 58 edits in all arms made something worse as a side effect.
- **No edit was aimed at building, and no note was left for the other cell.**
- **Edited harnesses ran out of calls as builders.** All 15 turns that ended with nothing written and no calls left ran in an edited harness (55 builds). None of the 35 builds in the seed harness did.
- **The seed's own write tool cuts a file at a line reading `@end`,** so 13 edits lost the tail of `prompt.md`. A builder writing a harness through that harness's own protocol trips on it.

### Cost

The ledger for the whole record stands at 22.20 dollars over 15110 model calls, against the cap of 25. That covers the smoke tests, the warm run, the calibration, the 20 runs of the block (5 of which cost nothing because every call was refused), the replacement replicate, the exam re-sit and the 20 assays. The 15 runs in the planned tables cost 12.62 dollars and 8038 calls by their own count, which leaves out retried calls. The exam with one call per task ran on a separate ledger after the owner opened a spend window: 1.47 dollars over 1009 calls. Block 2's part A ran on a ledger of its own under the owner's approval: 14.62 dollars over 10717 calls, against a cap of 20.

By arm, a run cost 0.64 dollars with stack, 0.79 solo, 0.81 with a seed builder, 0.97 under one score with free lineages and 1.00 under rival scoring (`results/explore.md`).

## Second count

A second agent session recounted replicates 0 to 2 from the logs and the plan's wording, without opening `analyze.py`. Its program and output are in `second_count/`, with a check of 90 turns and 62 gate decisions against the rules of each arm: no violation. `second_count/recount_final.out` is the same program pointed at the runs the planned tables use. It gives the same arm means, the same four contrasts with the same exact p, and the same verdict on P1 to P8 as `results/tables.md`.

It also read the referee for defects. What it found is in the limits below, and in deviation 2, which is its finding.

## Limits

- **A ceiling.** Every arm reached the top of the exam within one or two builds. Arms that all sit near 1.0 cannot be told apart, so the matches under P2, P3 and P5 are weak evidence of equality.
- **Three runs an arm** in the planned tables, one model, one machine, one day, six turns.
- **The gate is coarse.** With nothing changed, its score difference has a standard deviation of 0.072 and it kept 2 of 6 identical candidates.
- **The gate does not measure building.** A change that halves a cell's building is kept if the tasks still pass.
- **A score in the two code families could be forged.** Their hidden tests import the cell's code into the process that prints the result. A search of every harness snapshot and build trace found no sign that any cell tried, and every arm is equally exposed. The fix is to run cell code in a child process that never holds the result line. *Added 2026-11-24:* the hole is now shown, not only argued. Run offline on generated instances, the pilot's checker gives 1.000 to code that calls the hidden script's reporting function, in both code families, and 0.972 to bugfix code that returns an object equal to everything (`block2/checker_equivalence.out`). A second scan for the words those two forgeries need found one line, a builder printing example modules (`block2/forgery_rescan.out`). Neither scan covers the code solving cells wrote during episodes, which the pilot did not keep. Block 2 removes the hole.
- **A slow model ends an episode silently.** The 300-second limit zeroes an episode without a failed call on record. Outside the excluded run no episode in any analysed run hit it. *Added 2026-11-24:* block 2 charges a cell only for its own time and logs every kill.
- **The stack arm's two cells usually end on one harness,** which then sits the exam once and counts twice, as the plan says. That is more noise for that arm, not a bias.
- **The example tasks a builder sees** draw their seeds from a range that is not kept apart from the exam's. None of the 90 collided.
- **The model is reached through the `claude` command line tool,** which adds notes of its own to every call: a working directory, a scratchpad path, proxy and commit rules, and a reminder about the account. The referee starts the tool from a folder whose path matches the cell's own and puts one fixed line in front of every system prompt telling the cell to ignore those notes. They are the same in every arm.
- **Dollar figures are list prices** reported by the tool. The account is on a plan with a usage limit, and the block ran into it once. Block 2's part A ran into it too (its deviation 4).
- **The reading of what builders changed** is one reader's, on replicates 0 to 2.
- **The figure check is weak against small errors.** *Added 2026-11-24.* `check_numbers.py` shows that every decimal figure in this README, the note and the block 2 plan equals some number in an output file. It does not show that it equals the right one. Planting one wrong figure at a time, moved by 1 to 3 units in its last digit, it caught 24 of 60 in this README, 34 of 60 in the plan and 14 of 60 in the note, measured again after part A's results were added (`block2/check_numbers_power.out`; the first measurement, before them, gave 30, 27 and 17, so 60 plants pin a rate only to within about a tenth). The documents hold so many three-decimal numbers that a wrong figure often matches another true one. So read "every figure traces to an output" as a check against invented figures, not against mistyped ones.

## Block 2: part A run, part B not approved

Added 2026-11-24. [`block2/PLAN.md`](block2/PLAN.md) plans a second block in two parts. The owner approved part A, and it ran the same day; its results are below. Part B is not approved. The pilot's numbers above came from the files at commits `0ddfde4` and `ac808c4`. The referee in this folder has changed since, so a rerun of the pilot should check out those commits.

- **Two holes closed.** The code families' hidden checkers now give the cell's code only the inputs, and the referee compares what it returned (deviation from the frozen files, for block 2 only). On 2,520 honest instances the old and new checkers agree on every score, and no forgery scores above its honest counterpart (`block2/checker_equivalence.py`). The referee reads at most 8 MB of a hidden run's output and builds no set or dict from it, so returned values cannot stall it. Episodes are charged only for the cell's own time, not for time spent waiting on the model, with a hard wall limit that reruns the episode and then flags it; every attempt is logged with its clocks.
- **Guards tested by mutation.** `block2/mutate.py` removes 45 guards one at a time, and a test catches each (`block2/mutate.out`); two of them are input hygiene rather than security. Its first run found a guard no test covered: a symlink planted in an episode's work folder. A test for it was added.
- **An independent review** of these changes by another agent session found three defects and several smaller problems. The defects and most of the smaller problems were fixed before this text, and the plan states what is left: the plan understated part A's cost, the mutation script could not rerun its own output, and referee faults were neither carried into the assay rows nor counted by the analysis. It also found the stall above, an assay order that ran arms in blocks, an approval bound to the plan's text alone, and a gate that could discard a candidate exactly at its margin by floating-point error, a fault the pilot's gate had too.
- **Part A,** planned at about 14 dollars at list: assay the pilot's 19 fault-free final harnesses again, both slots, three fresh assays each, to test the building gap found after the runs (free lineages +0.020 against solo +0.492). The predictions, the analysis script (dry-run on the pilot's assays), a simulation of power and the hashes of every file it runs with were fixed in the plan before any data.
- **Part B,** about 42 dollars, sketched for a later decision: new runs with a gate that also pays for building.

### Part A: the building gap did not hold

The owner approved part A in the session's chat. The approval file (`block2/approval-partA.json`) names the plan's SHA-256, the run folder, a cap of 20 dollars, the approver and the date, and `run.py` checked it and every frozen file's hash before the first call. Part A ran from 05:27 to 08:00 UTC: 126 of 126 assays, no referee fault, no failed model call, no timeout. It cost 14.62 dollars over 10717 calls on its own ledger (`block2/partA/spend.json`); the rows' own counts give 14.54, the rest being attempts cut short by the usage limit below and one probe call. `block2/verify_partA.out` shows that every assay ran the archived harness it names, that every planned assay is there once, and that no task key repeats.

The planned analysis (`block2/results_a.md`, copied here):

| Arm | Runs | Run values (mean gain of 6 assays) | Mean | No edit, of 24 |
|---|---|---|---|---|
| twin-free-rival | 4 | +0.037, +0.160, +0.302, +0.346 | +0.211 | 4 |
| twin-free-collective | 4 | +0.419, +0.305, +0.145, +0.270 | +0.285 | 7 |
| twin-stack-collective | 3 | +0.436, +0.032, +0.000 | +0.156 | 11 of 18 |
| solo-pair | 4 | +0.269, +0.197, +0.516, +0.505 | +0.372 | 4 |
| twin-fixed-builder | 4 | +0.359, +0.456, +0.234, +0.575 | +0.406 | 1 |

The seed harness as builder gained +0.450 over 12 assays. The plan prints this beside the pilot's +0.331 for seed builders at turn 1 with no pass mark, and the two are not comparable: the checker and the time limit have changed since, and the service behind the model may have.

| Prediction | Difference | Exact p | Verdict |
|---|---|---|---|
| A1: free-lineage harnesses build worse than solo harnesses | -0.087 | 0.4286 | does not hold |
| A2: they build worse than seed-builder harnesses | -0.121 | 0.2286 | does not hold |
| A3: more of their assays make no edit than solo's | 0.292 against 0.167 | - | holds |

The plan named A1 failing as what counts against the pilot's reading. It failed. Measured on both slots and six times a run, harnesses from the free-lineage arm cannot be told apart from those of either control, so the pilot's "weakest builders measured" stands withdrawn. The direction is still the same, and part A could not have shown a small difference: with four runs an arm the plan's power simulation detects a true difference of 0.12 only 7 to 19 percent of the time, for a spread of 0.2 to 0.1 (`block2/power.out`). So part A withdraws the large gap; it does not show that there is none.

**Read after the planned analysis, not preregistered** (`block2/explore_a.py`, `.out`):

- **The pilot's single assays were not noise.** Over the 19 runs, the pilot's one assay of a slot-A harness correlates +0.703 with part A's mean of three on the same harness. Measuring once does not explain the pilot's gap by itself.
- **Two things moved it.** The pilot assayed slot A only, and in the free arm slot B builds better: +0.369 against +0.201 on slot A, while solo goes the other way, +0.314 against +0.429. And one free-arm harness had a bad single draw: -0.011 in the pilot, +0.517, +0.565 and +0.608 in part A. On slot A alone a gap remains, free minus solo -0.228 (exact p 0.2000). That contrast was chosen after the data and tests nothing.
- **Not editing is a trait of a harness.** Of the 32 harnesses assayed three times, 24 edited every time and 4 never did. If every harness had the pooled no-edit rate, about 14 and 0.4 would. The harnesses that never edited are 1 rival, 2 free, 1 stack (its two slots share one harness) and 1 solo; none from the seed-builder arm. Four of them spent all 16 calls of every build without writing a file. The fifth, rival r0 A, has a step limit of 12, below a build's 16 calls. The one other harness with that limit is free-collective r2 B, the one whose builds the pilot saw stop at 12 calls with nothing written (`results/changes/summary.md`). In part A it edited in all three assays, within 12 calls. So the limit alone does not stop a builder.
- **One assay says about half of what a harness can do.** The intraclass correlation of gains is 0.507: a single assay has a reliability of 0.51, a mean of six 0.86. Run values spread with a standard deviation of 0.113 to 0.243 by arm, inside the 0.1 to 0.2 the power simulation assumed.

**Deviations in running part A.**

1. **One probe call** before the launch, on part A's ledger, to check that the model answered (0.0003 dollars). It is in the ledger and in no row.
2. **Four processes, not one.** Part A ran as four processes, each taking every fourth assay of the planned order (`--shard i/4`); the plan's command shows one. The order within each repeat is the planned one, interleaved.
3. **One process crashed at start, before any model call.** The four unpacked the pilot's archives into one folder at the same moment, and one met a folder another had just made (`FileExistsError`). It was restarted within a minute, after a check that all 38 unpacked final harnesses match their hashes. The restart overwrote its first log; the error is quoted here from the session. `run.py` was not changed, since it is frozen.
4. **The account ran out of allowance for a while,** as it did in the pilot. The frozen code waited, probed, and reran each cut step from the start: 3 builds and 5 candidate episodes, in 4 rows (`block2/verify_partA.out`). The plan says such a refusal "reruns the assay, as in the pilot". The code reruns only the cut build or episode, as the pilot's code did. No rerun depends on a score.
5. **Added after the data and not planned:** `block2/verify_partA.py` and `block2/explore_a.py`.

| Path | What it holds |
|---|---|
| `block2/PLAN.md` | The plan, predictions, power, costs, the backend question, the approval rule |
| `block2/checker_equivalence.py`, `.out` | Old checker against new, honest solutions and forgeries |
| `block2/mutate.py`, `.out` | The mutation check of the referee's guards |
| `block2/selftest.out` | The task self-test with the new checker |
| `block2/forgery_rescan.py`, `.out` | The second scan of the pilot's archives |
| `block2/analyze_a.py`, `analyze_a_dryrun.md` | Part A's analysis, and its dry run on the pilot's single assays |
| `block2/power.py`, `.out` | Power of the planned test, by simulation |
| `block2/costs.py`, `.out` | The plan's cost figures, from the pilot's logs |
| `block2/freeze.py` | Writes the hashes of the files part A runs with into the plan, or checks them |
| `block2/approval-partA.json` | The owner's approval of part A, bound to the plan's hash, the run folder, the cap and a date |
| `block2/partA/` | Part A's 126 rows (`assay2-partA-*.jsonl`), its ledger, the four processes' logs, and every build trace and harness snapshot of its assays (`builds.tar.gz`) |
| `block2/results_a.md` | Part A's planned analysis |
| `block2/verify_partA.py`, `.out` | Checks of part A's rows: harness hashes, completeness, reruns, spend. Written during the run, not planned |
| `block2/explore_a.py`, `.out` | Part A read after the planned analysis: retest, slots, reliability, no-edit harnesses. Not planned |
| `block2/check_numbers_power.py`, `.out` | How often the figure check catches a planted error |
| `tests/test_units.py` | Fast tests of the gate, seeding, decoding, checkers, the brain server, the fault rules, the approval rule and the plan's hashes |

## Disclosure

Produced by an AI agent session after the owner handed the programme over on 2026-11-17. The session set the spend cap itself and told the owner before the first relay run. Agent sessions working from written briefs wrote the task families, the second count with its review of the referee, and the reading of what builders changed. The lead wrote the referee, the plan, the analysis and this record, and ran everything. No person has reviewed it.
