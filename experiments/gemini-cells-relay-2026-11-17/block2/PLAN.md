# Block 2: plan

Status: **proposal, not approved, not run.** Written 2026-11-24, a week after the pilot, and revised the same day after an independent review. Nothing here has been run on a model. Part A starts only with the owner's yes for that run (an approval file bound to this text, see "Approval"). Part B is laid out so it can be judged, but is not proposed for approval until part A has been read.

## Why a second block

The pilot (this record's README) left one striking result and one weak one.

- **Weak: the twin effect on tasks.** Every arm reached the top of the exam within one or two builds. The visible exam went from 0.501 for the seed to between 0.886 and 0.994. With that ceiling, "the controls matched the twins" says little about a harder setting.
- **Striking, but found after the runs were seen: building.** The builder assay gives a run's final harness one build turn on a fresh seed harness and measures the gain. Over every fault-free run, harnesses built by twins under one score with free lineages gained +0.020 on average, against +0.492 for harnesses from the solo control and +0.474 from the seed-builder control. Every free-arm assay (highest +0.092) was below every solo assay (lowest +0.275). That is the opposite of the reciprocal loop [pull request 27](https://github.com/Moissanite-Labs/weft-loom/pull/27) hoped for. But the comparison was not planned, each harness was assayed once, and only slot A was assayed.

The assay has room where the exam does not: it starts from the seed at about 0.5, and pilot gains ran from -0.011 to +0.639. So block 2 makes building its primary measure. Part A asks whether the pilot's building result holds when the same harnesses are measured again. Part B, if it is wanted, asks whether arms produce such harnesses reliably, and whether a gate that also measures building changes that.

## What changed in the instrument since the pilot

All offline, no model called. Each change has tests. `block2/mutate.py` removes 45 guards one at a time and a test catches each (`block2/mutate.out`); two of the 45 are input hygiene rather than security.

1. **Hidden checkers no longer share a process with cell code.** In the pilot, the code families (bugfix, spec) ran the cell's code in a process that also held the expected results and the function that printed the score. Code a cell wrote could have called that function and claimed full marks. The pilot's forgery scan found no sign of this, but the hole was real: `block2/checker_equivalence.py` shows the pilot's checker giving 1.000 to such code in both families, and 0.972 to bugfix code that returns an object equal to everything. Now the sandboxed process gets only the inputs and reports what each call returned as plain data, and the referee compares. On 2,520 generated instances (14 honest variants over the two families, each on 60 seeds at 3 levels) the old and new checkers give the same score on every instance. No forgery scores more than an honest solution named beside it (`block2/checker_equivalence.out`). The task self-test gives the same table as the pilot's (`block2/selftest.out`).
2. **The new checker cannot be made to stall the referee.** It reads at most 8 MB of a hidden run's output, and it never builds a set or a dict from what the cell returned: numbers chosen to collide in a hash make that quadratic. The independent review of these changes reported a solution that held the referee for about 97 seconds that way, before this fix. No expected result in either code family is a set or a dict, so this changes no score.
3. **A slow model no longer zeroes an episode.** The pilot killed an episode at 300 seconds of wall time, model calls included, with nothing on record to blame. Now the cell is charged only for its own time: wall time minus the time a model call was in flight. A hard limit of 3 times that on plain wall time catches a stalled backend. A kill at the hard limit runs the episode or build again, at most twice, and after that the result carries `referee_fault`. Reruns after a usage-limit refusal are counted apart and do not use up those two. The kept result records `timed_out`, the clocks at the kill (`kill`) and `model_wait_s`, and every attempt that was run again is listed in `attempts` with its own clocks. Boot checks carry the same fields. An empty prompt is refused without asking the model, since a prompt that makes the backend fail would otherwise buy the cell uncharged time. A model call still in flight when a cell is killed is awaited for up to 30 seconds so its cost lands in the episode; the ledger counts it in any case.
4. **The gate rule is one tested function** (`relay.gate`). It now compares the difference rounded to 9 decimals, so a candidate exactly `margin` below the incumbent is kept; in the pilot, floating-point error could discard it. New tests also cover commit-then-reveal seeding recomputed from the revealed secret, server-side prompt clipping, a symlink planted in an episode's work folder, the checker through the real sandbox, and `run.py assay2` end to end with a scripted model.

The pilot's numbers were produced by the files at commit `0ddfde4`, and by `ac808c4` for replicate 4 and the assays. The pilot's results and its reading of them are unchanged. Its README gained a dated section on block 2 and two dated notes in its limits.

## Part A: measure the pilot's harnesses again

**Question.** Are the final harnesses that twins under one score with free lineages built for each other weaker builders than those of the solo control and of the seed-builder control?

**Harnesses.** The final harnesses of the 19 fault-free pilot runs, read from the record's packed archives (`results/runs/*/artifacts.tar.gz`), both slots: 4 runs for each arm, 3 for stack. Plus the seed harness itself as a builder, for scale.

**Procedure.** The pilot's assay, unchanged except for the instrument fixes above: a fresh seed harness as the target, a fresh benchmark report of it as the builder's information, one build turn with the brief of the arm with one score and free lineages, then the gate's paired benchmark of seed and candidate on 9 fresh tasks (3 per visible family, level 3). Every assay draws a new per-assay secret, so its tasks are new. Three assays per slot per run (6 per run, 114 in all), and 12 of the seed as builder: 126 assays. They run repeat by repeat, so a run cut short leaves every harness with the same number of assays give or take one. Within a repeat the order is shuffled from a seed made of a fixed phrase, the tag and the repeat, and the seed's 12 assays are spread four to a repeat, so drift in the backend over the hours is not tied to arm. Each row logs its position, its secret and the base benchmark. Command: `python3 run.py assay2 --root R2 --tag partA --approval APPROVAL.json`.

**Model.** claude-haiku-5-5 through the `claude` command line tool, tools and thinking off, as in the pilot. The harnesses were built for this model; measuring them with another would be a different question. The model identifier is the same as in the pilot. Whether the service behind it changed in a week cannot be checked from here. The 12 seed assays are printed beside the pilot's first-turn seed-builder gains (mean +0.331 over 15) for comparison, with no pass mark.

**Measures.** A gain is the candidate's mean minus the seed's mean on the same tasks when the candidate reached the benchmark, and 0 when it did not (no edit, invalid, or failed to boot), as in the pilot. A run's value is the mean gain of its 6 assays. An assay whose build, boot or any benchmark episode carries `referee_fault` is left out, and the analysis prints how many by arm. Only repeats that every run finished on both slots are used; a missing slot or run is printed as a warning. `block2/analyze_a.py` is the analysis. It was run on the pilot's single assays as a dry run (`block2/analyze_a_dryrun.md`), and reproduces the record's exploratory means.

**Predictions.** Fixed here, before any assay of part A.

| # | Prediction | Holds when |
|---|---|---|
| A1 | Free-lineage collective harnesses build worse than solo harnesses | free mean below solo mean, exact two-sided permutation p at most 0.05 over the 4 + 4 run values |
| A2 | They build worse than seed-builder harnesses | the same against the 4 seed-builder runs |
| A3 | Part of the gap is builders that make no edit | the share of free-arm assays without an edit is above the solo arm's |

With 4 runs an arm the smallest attainable p is 0.029, so A1 and A2 hold only if every free run is below every run of the other arm. Rival and stack are reported without a prediction.

**What counts against the pilot's reading.** A1 failing. If free and solo overlap when each harness is measured six times, the pilot's separation came from measuring each harness once, and this record's note should say so.

**Power.** From `block2/power.py` (simulation of this exact test, counting only rejections in the predicted direction; `block2/power.out`), with 4 runs an arm: if the true difference is the pilot's 0.47, A1 is detected 63 to 99 percent of the time for a per-run spread of 0.2 to 0.1. If it is half that, 18 to 65 percent. The pilot's single assays had a spread of 0.048 in the free arm and 0.156 in the solo arm. Averaging 6 assays a run should keep the spread near the low end, but that is a hope, not a measurement. Part A tests these 19 harnesses. It cannot say whether the arms would produce such harnesses again. That is part B's question.

**Cost.** Pilot assays cost 0.112 dollars on average at list price, counting the seed benchmark each assay starts with (20 assays, 2.244 dollars; `block2/costs.out`). 126 assays: about 14 dollars, before retried calls. Proposed cap: 20 dollars, on a ledger separate from the pilot's.

**Stops.** The ledger refuses calls past the cap. A usage-limit refusal pauses and reruns the assay, as in the pilot. Faults are handled as in "Measures".

## Part B: new runs (not proposed for approval yet)

Only worth running if part A leaves the building question open or confirms the gap. Sketched here so the choice can be made with the cost in view.

- **Arms, 6 runs each.** solo-pair, twin-free-collective, twin-fixed-builder, and one new arm, **twin-collective-buildgate**: the gate also measures building. Each gate gives the candidate and the incumbent one build turn on a fresh seed, and adds their build gains to their task scores. The brief says so. This is the direct test of the exact model's point that a cell has a reason to improve its twin's building only when building is paid for. It is not built yet. It would get offline tests, and the mutation check would be extended to it, before any run.
- **Primary measure.** The assay of each run's final harnesses, 6 per run as in part A. Secondary: the visible, held-out and one-call exams.
- **Power.** With 6 runs an arm: a difference of 0.24 is detected 45 to 97 percent of the time for a spread of 0.2 to 0.1.
- **Cost at list** (`block2/costs.out`). The 19 fault-free pilot runs cost 0.85 dollars on average. 18 plain runs is about 15 dollars. 6 build-gate runs is about 11, since each gate adds two build probes. 144 final assays is about 16. In all about 42 dollars, so a cap near 50.
- **Backend.** See below. Part B is where a change of model could be considered, because it builds new harnesses.

## Backend: Haiku through the command line tool, or Inkling 2 Mini on Tinker

The team is moving its model work to Inkling 2 Mini, with training on Tinker and an owner's yes for every paid run ([issue 39](https://github.com/Moissanite-Labs/weft-loom/issues/39), [issue 40](https://github.com/Moissanite-Labs/weft-loom/issues/40)). For this experiment:

- **Part A must use the pilot's model,** because it measures harnesses built for that model.
- **For part B, Inkling 2 Mini is possible but not free of work.** It needs a backend with the same contract (`call(system, prompt)` returning the reply, cost and token counts). The client code in [pull request 46](https://github.com/Moissanite-Labs/weft-loom/pull/46) has run against the service, by that pull request's account, and is the obvious base. It also needs a fresh calibration of the seed and reference harnesses, because the pilot's thresholds were set on Haiku. Pull request 46 reports that the untrained model opens a thinking block and runs out of tokens under a small cap. The relay's protocol asks for one short action per reply, so the same forcing of the answer opening, or a larger cap, would be needed. In its favour: no account usage limit, which cost the pilot a replicate, and a published price per token.
- **A use only Tinker offers.** Each cell's "harness" could include a small LoRA adapter, so that the builder writes training data for its twin as well as text. That would carry pull request 27's question from prompts to weights. It is an idea in the note (G15), not part of this plan.

## Approval

`run.py assay2` refuses to start unless `--approval` names a JSON file holding `plan_sha256` (the SHA-256 of this file, exactly as committed), `tag` (`partA`), `root` (the absolute path of the run folder, so one ledger and one cap), `cap_usd` (at most 50), `approved_by` and `date`. It also refuses if any file listed under "Frozen files" differs from its hash. So an approval covers one text of this plan, the code it names, and one run folder, and any later edit to either needs a new approval. Commit the approval file into the record with the run's output.

## What is not settled by either part

- Whether a reciprocal loop appears with a longer horizon than 6 turns, or a benchmark with no ceiling at all.
- Whether any of this holds for a model other than the one the harnesses were built with.
- Whether a cell could make the backend fail on purpose. Time spent waiting on a failing call is not charged to the cell, so such a cell would get that time free and could reach the hard limit, which reruns the task. The one such prompt found, an empty one, is refused. Retry time after other failures is still not charged.
- Whether the assay itself is a fair test of a harness built for another target. The assay gives every harness the same seed target and the same brief, which is not the brief its own arm used.

## Frozen files

Written by `block2/freeze.py`. `run.py assay2` checks every line before it starts.

```
72db253a8552fd6dcebcde54ddbbc0498285f66936262e000e9bc6c124041dfc  block2/analyze_a.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  referee/__init__.py
49c2ea8b38f9cb030216291df8f487850b4e0ee768eb835bcf32d32b52418b98  referee/bench.py
c4bb1e124fc34af5f7667ea44000c969201a762261bc8f2dd114214f539a5d7b  referee/brain.py
435508c50868135850ae5b381a3f56b6e2d10fa6c1ade56811d9c6b07049ce57  referee/cellapi.py
b17f0f6d1dc437d554f42c667c1a94c09d3117cea9d5b02e4fdd5ac7e4754e1a  referee/relay.py
3781bf2822146f19622d872b7c978cedc59c9ac4e612a7cadcb63d4483fba3b0  referee/sandbox.py
4dba49eba87f053187017696c996ecca887ad2eb64c406a3eefab66348507372  referee/tasks/__init__.py
7e5ab0dd1a23167922e9f9fe0c7b28ef7f50f6cf697219ea0528f17349af088a  referee/tasks/_bugpool_a.py
b299eb899d4ee19eab4a5aadde7cddbf2c403779d332a6dce4642225029f995d  referee/tasks/_bugpool_b.py
21e2e17f900296a3a904c8880f6d383dcf7d67a14f7453d584bfa6827ad79a12  referee/tasks/_specpool_a.py
659bf881ecb0da7cd1dc3ddcdc2081c99517b8dca1bd63d384d81d813732bf1c  referee/tasks/_specpool_b.py
02cd58935ff59bd0271bd324fab2ca4f543198ab0016e04b81027831f1a65a07  referee/tasks/_util.py
1105f52d8dc0c8e34a7ca2c3157e1641fc3507d1fc1965900335396b57339c9b  referee/tasks/bugfix.py
9b1a1132c7a9f95a4e2553f5bd449f1b711cc9fc3acf8d1c2cc1af7d41ad66e8  referee/tasks/ledger.py
c27ed2f3844d5987bf3dfeb91b237fae9139c6046adbab5e48e38f6befcb5041  referee/tasks/logwin.py
9655ab900b95adfd1b9f72b0acb2dee1d8737e3804312c1ec75af4e8a7fbe50a  referee/tasks/selftest.py
f91a665384737d6cd3a09255bed2cb18b1e37d8f5374a385961db5217f8a0cb3  referee/tasks/spec.py
be1015fd12f7d5b298a407c7bc301deb587b0c55f81bac3001709a2e932316b5  referee/tasks/stock.py
5e80f132b36fb397edd52464946bc1e459c2e196292919dbb23667a33f468c89  run.py
ba894b5afd76df787bec3bfbdfa42c7a76fb1bc77ed931b10dfd9397affe3f93  seed/agent.py
9f85ed0362874950eea83c76d53d38867db2b9b61725281d5ebf561f49fadb7d  seed/prompt.md
dda30265847d69923febab964fc71fd65783045fd0069c98d237abcd64bb54aa  seed/tools/sh.py
733ec3b15b28f9b41e6ef4e7754bf5c6cd2861fd02fdaf3ec245b9315c2baf2d  seed/tools/write.py
```
