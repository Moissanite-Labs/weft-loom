# Block 2: plan

Status: **proposal, not approved, not run.** Written 2026-11-24, a week after the pilot. Nothing here has been run on a model. Part A starts only with the owner's yes for that run (an approval file bound to this text, see "Approval"). Part B is laid out so it can be judged, but is not proposed for approval until part A has been read.

## Why a second block

The pilot (this record's README) left one striking result and one weak one.

- **Weak: the twin effect on tasks.** Every arm reached the top of the exam within one or two builds. The visible exam went from 0.501 for the seed to between 0.886 and 0.994. With that ceiling, "the controls matched the twins" says little about a harder setting.
- **Striking, but found after the runs were seen: building.** The builder assay gives a run's final harness one build turn on a fresh seed harness and measures the gain. Over every fault-free run, harnesses built by twins under one score with free lineages gained +0.020 on average, against +0.492 for harnesses from the solo control and +0.474 from the seed-builder control. Every free-arm assay (highest +0.092) was below every solo assay (lowest +0.275). That is the opposite of the reciprocal loop PR 27 hoped for. But the comparison was not planned, each harness was assayed once, and only slot A was assayed.

The assay has room where the exam does not: it starts from the seed at about 0.5, and pilot gains ran from -0.011 to +0.639. So block 2 makes building its primary measure. Part A asks whether the pilot's building result holds when the same harnesses are measured again. Part B, if it is wanted, asks whether arms produce such harnesses reliably, and whether a gate that also measures building changes that.

## What changed in the instrument since the pilot

All offline, no model called. Each change has tests, and `block2/mutate.py` shows that removing any of 30 guards makes a test fail.

1. **Hidden checkers no longer share a process with cell code.** In the pilot, the code families (bugfix, spec) ran the cell's code in a process that also held the expected results and the function that printed the score. Code a cell wrote could have called that function and claimed full marks. The pilot's forgery scan found no sign of this, but the hole was real: `block2/checker_equivalence.py` shows the pilot's checker giving 1.000 to such code in both families, and 0.972 to bugfix code that returns an object equal to everything. Now the sandboxed process gets only the inputs and reports what each call returned as plain data, and the referee compares. On 2,520 generated instances (14 honest variants over the two families, each on 60 seeds at 3 levels) the old and new checkers give the same score on every instance. No forgery scores more than an honest solution named beside it (`block2/checker_equivalence.out`). The task self-test gives the same table as the pilot's (`block2/selftest.out`).
2. **A slow model no longer zeroes an episode.** The pilot killed an episode at 300 seconds of wall time, model calls included, with nothing on record to blame. Now the cell is charged only for its own time: wall time minus the time a model call was in flight. A hard limit of 3 times that on plain wall time catches a stalled backend. A kill at the hard limit runs the episode or build again, at most twice, and after that the row carries `referee_fault`. Every kill is logged with both clocks (`timed_out`, `model_wait_s`).
3. **The gate rule is one tested function** (`relay.gate`), and new tests cover its boundary, commit-then-reveal seeding recomputed from the revealed secret, server-side prompt clipping, and a symlink planted in an episode's work folder.

The pilot's numbers were produced by the files at commit `0ddfde4`, and by `ac808c4` for replicate 4 and the assays. The pilot's README is unchanged by any of this.

## Part A: measure the pilot's harnesses again

**Question.** Are the final harnesses that twins under one score with free lineages built for each other weaker builders than those of the solo control and of the seed-builder control?

**Harnesses.** The final harnesses of the 19 fault-free pilot runs, read from the record's packed archives (`results/runs/*/artifacts.tar.gz`), both slots: 4 runs for each arm, 3 for stack. Plus the seed harness itself as a builder, for scale.

**Procedure.** The pilot's assay, unchanged except for the instrument fixes above: a fresh seed harness as the target, a fresh benchmark report of it as the builder's information, one build turn with the brief of the arm with one score and free lineages, then the gate's paired benchmark of seed and candidate on 9 fresh tasks (3 per visible family, level 3). Every assay draws a new per-assay secret, so its tasks are new. Three assays per slot per run (6 per run, 114 in all), and 12 of the seed as builder: 126 assays. They run repeat by repeat, so a run cut short leaves every harness with the same number of assays give or take one. Command: `python3 run.py assay2 --root R2 --tag partA --approval APPROVAL.json`.

**Model.** claude-haiku-5-5 through the `claude` command line tool, tools and thinking off, as in the pilot. The harnesses were built for this model; measuring them with another would be a different question. The model identifier is the same as in the pilot. Whether the service behind it changed in a week cannot be checked from here, so the 12 seed assays also give a check against the pilot's first-turn seed-builder gains (mean +0.331 over 15).

**Measures.** A gain is the candidate's mean minus the seed's mean on the same tasks when the candidate reached the benchmark, and 0 when it did not (no edit, invalid, or failed to boot), as in the pilot. A run's value is the mean gain of its 6 assays. `block2/analyze_a.py` is the analysis. It was run on the pilot's single assays as a dry run (`block2/analyze_a_dryrun.md`), and reproduces the record's exploratory means.

**Predictions.** Fixed here, before any assay of part A.

| # | Prediction | Holds when |
|---|---|---|
| A1 | Free-lineage collective harnesses build worse than solo harnesses | free mean below solo mean, exact two-sided permutation p at most 0.05 over the 4 + 4 run values |
| A2 | They build worse than seed-builder harnesses | the same against the 4 seed-builder runs |
| A3 | Part of the gap is builders that make no edit | the share of free-arm assays without an edit is above the solo arm's |

With 4 runs an arm the smallest attainable p is 0.029, so A1 and A2 hold only if every free run is below every run of the other arm. Rival and stack are reported without a prediction.

**What counts against the pilot's reading.** A1 failing. If free and solo overlap when each harness is measured six times, the pilot's separation came from measuring each harness once, and this record's note should say so.

**Power.** From `block2/power.py` (simulation of this exact test, `block2/power.out`), with 4 runs an arm: if the true difference is the pilot's 0.47, A1 is detected 63 to 99 percent of the time for a per-run spread of 0.2 to 0.1. If it is half that, 18 to 65 percent. Averaging 6 assays a run should keep the spread near the low end, but that is a hope, not a measurement. Part A tests these 19 harnesses. It cannot say whether the arms would produce such harnesses again. That is part B's question.

**Cost.** Pilot assays cost 0.081 dollars on average at list price (20 assays, 1.63 dollars; `block2/costs.out`). 126 assays: about 10 dollars. The approval sets the cap. Proposed cap: 15 dollars, on a ledger separate from the pilot's.

**Stops.** The ledger refuses calls past the cap. A usage-limit refusal pauses and reruns the assay, as in the pilot. Assays killed at the hard wall limit twice over are kept and flagged, and the analysis reports how many there were.

## Part B: new runs (not proposed for approval yet)

Only worth running if part A leaves the building question open or confirms the gap. Sketched here so the choice can be made with the cost in view.

- **Arms, 6 runs each.** solo-pair, twin-free-collective, twin-fixed-builder, and one new arm, **twin-collective-buildgate**: the gate also measures building. Each gate gives the candidate and the incumbent one build turn on a fresh seed, and adds their build gains to their task scores. The brief says so. This is the direct test of the exact model's point that a cell has a reason to improve its twin's building only when building is paid for. It is not built yet. It would get offline tests, and the mutation check would be extended to it, before any run.
- **Primary measure.** The assay of each run's final harnesses, 6 per run as in part A. Secondary: the visible, held-out and one-call exams.
- **Power.** With 6 runs an arm: a difference of 0.24 is detected 45 to 97 percent of the time for a spread of 0.2 to 0.1.
- **Cost at list** (`block2/costs.out`). The 19 fault-free pilot runs cost 0.85 dollars on average. 18 plain runs is about 15 dollars. 6 build-gate runs is about 11, since each gate adds two build probes. 144 final assays is about 12. In all about 38 dollars, so a cap near 45.
- **Backend.** See below. Part B is where a change of model could be considered, because it builds new harnesses.

## Backend: Haiku through the command line tool, or Inkling 2 Mini on Tinker

The team is moving its model work to Inkling 2 Mini, with training on Tinker and an owner's yes for every paid run (issues 39 and 40). For this experiment:

- **Part A must use the pilot's model,** because it measures harnesses built for that model.
- **For part B, Inkling 2 Mini is possible but not free of work.** It needs a backend with the same contract (`call(system, prompt)` returning the reply, cost and token counts). The client code in PR 46 has run against the service and is the obvious base. It also needs a fresh calibration of the seed and reference harnesses, because the pilot's thresholds were set on Haiku. PR 46 found that the untrained model opens a thinking block and runs out of tokens under a small cap. The relay's protocol asks for one short action per reply, so the same forcing of the answer opening, or a larger cap, would be needed. In its favour: no account usage limit, which cost the pilot a replicate, and a published price per token.
- **A use only Tinker offers.** Each cell's "harness" could include a small LoRA adapter, so that the builder writes training data for its twin as well as text. That would carry PR 27's question from prompts to weights. It is an idea in the note, not part of this plan.

## Approval

`run.py assay2` refuses to start unless `--approval` names a JSON file holding `plan_sha256` (the SHA-256 of this file, exactly as committed), `tag` (`partA`) and `cap_usd`. So an approval covers one text of this plan and one run, and any later edit to the plan needs a new approval. Commit the approval file into the record with the run's output.

## What is not settled by either part

- Whether a reciprocal loop appears with a longer horizon than 6 turns, or a benchmark with no ceiling at all.
- Whether any of this holds for a model other than the one the harnesses were built with.
- Whether the assay itself is a fair test of a harness built for another target. The assay gives every harness the same seed target and the same brief, which is not the brief its own arm used.
