# Preregistration: signed feedback in exact repair

Status: written before any model was run. At this point the harness has only been run with deterministic mock proposers. The commit that holds this file fixes the plan. Later edits go in a dated "Amendments" section at the end and never replace the text above it.

## Hypothesis

An exact checker rejects a model's answer to a rational difference-constraint problem. If the feedback names which constraints failed, where, and by what signed exact amount, the model repairs the answer in fewer rounds than if the feedback names only which constraints failed and where.

Why the comparison is C against B: with a pass or fail answer alone, the search needs many more queries, roughly growing with the dimension of the problem. That ordering is a source claim from classical oracle-complexity results and is not tested here. The question here is whether, once the constraint and place are known, the signed amount adds anything for a small language model working in context.

## Task

The task is a system of constraints `xU - xW <= c` over rational numbers, with `c` a fraction. A generator plants a feasible point and makes some constraints tight at it. One constraint named `goal` forces a required gap between two named variables, so the all-zero answer always fails it.

The checker needs only the instance and the candidate. It computes every constraint's left side minus its bound with exact fractions and lists those above zero. The planted point is used for generation and tests, never by the checker.

The model must reply with one line per variable, like `x0 = 3/2`, and nothing else. Parsing is strict. A reply that cannot be read counts as a failed round and receives the same message in every arm.

## Arms

The first message is identical in every arm. The arms differ only in the text sent after a failed round.

- A: the verdict only. It says the answer failed.
- B: the verdict and the list of violated constraints, each written out with its place (the variables and the bound).
- C: B plus the signed exact excess for each listed constraint, as left side minus bound, shown with a plus sign when positive.
- D: C with every sign flipped. This is the control for whether the model reads the sign or only the size.

## Design

- Rounds: k = 4. Round 1 is the model's first answer and is identical across arms. Rounds 2 to 4 are repairs. A unit is one (model, arm, instance).
- Temperature 0, one fixed server seed, one request per round, the full chat history sent each time.
- Two difficulty levels, 100 instances each, per model.
  - S: 4 variables, 4 cycle constraints plus 2 extra, plus the goal (7 in all). Bounds are multiples of 1/2.
  - M: 6 variables, 6 cycle constraints plus 5 extra, plus the goal (12 in all). Bounds are multiples of 1/6.
- Seeds: S uses 100000 to 100099 and M uses 200000 to 200099. The same instances are used for all four arms and for every model.
- Per model: 800 units and at most 3200 requests.
- Each model is its own test. Nothing is pooled across models or across the two levels.
- Sizes, seeds, k and the prompts are fixed by this file. They are not tuned after seeing results.

## Metrics

Primary, per arm: the number of instances solved within k rounds.

Secondary, reported and not used for the decision:

- Rounds to solve, with unsolved units counted as k + 1. Compared with an exact paired sign-flip test.
- Repeated identical answers: the share of consecutive round pairs in which the parsed candidate is the same as the round before.
- Unreadable replies: the share of rounds whose reply failed parsing, per arm.

## Comparisons

- Test: C against B on the primary metric.
- Check: B against A. Expected direction is that B does at least as well as A.
- Check: D against C. Expected direction is that C beats D.

The checks do not change the decision. They are reported next to it. If D matches C, any gain of C over B is not evidence that the model uses the sign.

## Paired test and threshold

For each model and level, count the instances solved by C and not by B (first only) and by B and not by C (second only). Instances solved by both or neither carry no information and are left out.

The test is the exact one-sided binomial sign test on those discordant pairs, with the null that each discordant pair is equally likely to go either way. The threshold is 0.025 per level, which splits 0.05 across the two levels.

The analysis script `analyze.py` applies the rule below and prints the verdict next to the counts.

## What counts for and against the claim

For one model and level, in this order:

1. Floor or ceiling: every arm solves 5 percent or fewer, or every arm solves 95 percent or more. The level cannot test the claim and the result says so.
2. Too few discordant pairs: fewer than 10. The level cannot test the claim.
3. Supports: p is 0.025 or lower in the direction of C.
4. Against: p is above the threshold and C solved no more instances alone than B did, or B beats C at 0.025 or lower.
5. Otherwise inconclusive.

For one model overall: supports if at least one level supports and none is against. Against if every level is against. Mixed if one supports and another is against. Anything else is not decided.

A result against the claim is reported with the same weight as one for it. If both levels are at the floor or the ceiling for a model, the report says the model was not informative at these sizes and the sizes are not changed.

## Limits

- One task family. A positive result says nothing about proofs, code or other checkers.
- In-context repair only. No weights are updated.
- Small models only. The result need not hold for larger models.
- The mock proposers in the self-test are built to use or ignore the signed amount. They test the harness and say nothing about models.
- A model that reasons at length may run out of its token budget before it answers. That shows up as unreadable replies and is reported per arm.

## Harness checks already done (verified)

Run in the working copy: `python3 -O -B -W error -m unittest discover -s tests`, `python3 -O -B -W error selftest.py` and `python3 mutate.py`.

- The unit tests and the self-test pass.
- With a mock that ignores feedback, all four arms solve the same units in the same round, and some units solve and some do not, so the tie is not trivial.
- With a mock that uses the signed amount, C beats B and B beats D, each at p below 0.01 on 40 instances.
- With a mock that reads only the size of the excess, C and D tie exactly.
- Each of 28 deliberate breaks to the checker, generator, parser, arms, runner, resume logic, tests and analysis turns at least one check red.

## Models and settings

Chosen on 2026-11-20 from a pilot. All server runs use one slot, all layers on the GPU, a context of 8192, and the runner's fixed temperature 0 and seed 0.

- Small model: gemma-4-E4B-it-Q8_0. Server flags: `-np 1 -ngl 99 -c 8192 --reasoning on --reasoning-budget 1000`. Runner: `--max-tokens 1400`.
- Mid-size model: Qwen3.8-27B-AD-Q4_K_M. Server flags: `-np 1 -ngl 99 -c 8192 --reasoning off`. Runner: `--max-tokens 1024`.

The runner reads only the final answer text. Parsing stays strict, so a reply with a decimal, a lead-in sentence or visible working counts as unreadable.

The mid-size model is run first. The small model's run takes about 19 hours on the test machine and is run after it. If the small model's run is not completed, the report says so and the small model is not counted.

### Pilot

A pilot on seeds outside the registered ranges (900000 to 900005 and 910000 to 910005) was used only to choose these models and settings. Its outcomes are not part of the result. The pilot is written up in PILOT.md.

## Amendments

None.

> Automated posting by agentic team with human oversight.
