# Repair-signal training loop, design and dry run (2026-11-21)

## Question

When a model must repair a rejected answer to a rational difference-constraint puzzle, and may answer only with the repaired assignment under one small token cap, does training on feedback that gives the exact amount of each violation let it repair more often than training on feedback that names only the violated constraints?

The record holds the preregistered plan and the training loop that would run it on Inkling 2 Mini through the Tinker service, with a harness that is built and tested but has not been used on any model. Every prompt that is sampled from ends with the model's turn already opened for an answer (the forced opening), because the untrained model always opens a thinking block and no switch turns it off.

## Status

`design`. The plan and the code exist. No model has been trained, and nothing here has called a paid service or read a key. The untrained model was sampled once, for free, on pilot evaluation seeds only, with a local quantised copy: see [local-baseline](local-baseline/README.md). That is an exploratory measurement and not a result.

## Preregistration

[PREREG.md](PREREG.md). It is registered when this record is merged to the default branch, and until then edits made in answer to review are part of review. A paid run starts only after the owner approves that run, with its own run id and spend ceiling. The registered decision id is in `decisions.json`, and the plan cites the SHA-256 of that file (a test checks that the two agree).

## How to rerun

Requirements: Python 3.10 or newer and the standard library. The paid backend imports its service library only when it builds a real client, so nothing below needs a key or a network.

Run these from this folder.

```
python3 -I -B dryrun.py
python3 -I -B -m unittest discover -s tests
python3 -I -B mutate.py
python3 -I -B cost.py
```

Output is identical under `python3 -I -B`, `python3 -I -O -B` and `python3 -I -B -W error`. The dry run also takes `--record PATH`, which checks the vendored `vendor/rsig.py` against the same file in the earlier record.

The plan's other numbers come from these scripts. `power.py 1000` is exact and takes a few minutes. `checks/power_crosscheck.py` needs scipy, shares no code with `power.py` and agrees with it to 0.000035.

`checks/e_floor.py` and `checks/rule2_ties.py` print the chance floor on text E and the tie counts in the canonical repair.

`checks/targets.py` prints the rule split of the training targets, the mean amounts of texts C and E, the coverage of the first rule by the number of variables moved, and the one-subtraction count. `power.py 400` prints the 0.35 the plan quotes for the earlier set size.

```
python3 -I -B power.py 1000
python3 -I -B power.py 400
python3 -I -B checks/power_crosscheck.py
python3 -I -B checks/e_floor.py
python3 -I -B checks/rule2_ties.py
python3 -I -B checks/targets.py
```

`python3 -I -B local-baseline/check_seeds.py` checks that the committed local baseline holds pilot evaluation seeds only.

`cost.py --venv-python PATH` counts with the real tokenizer through a worker that imports tml_renderers. The layout test in `tests/test_layout_real.py` also needs that package and is skipped without it (6 tests). The layout test and the tokenizer cost count were run once with a Python that has the package, and all 6 layout tests passed.

The outputs are committed under `data/`: `dryrun.txt` (`dryrun.py`), `cost-rule.txt` (`cost.py`), `cost-tokenizer.txt` (`cost.py --venv-python PATH`, with a Python that has tml_renderers), `targets.txt`, `e_floor.txt`, `rule2_ties.txt` and `power-400.txt` (the script of the same name, run as listed above).

The dry run is deterministic and runs on any machine. It was run here on one Apple laptop with the system Python.

## Results

None yet. No model has produced a result for this question.

The dry run checks the harness with stand-in policies. It says nothing about any model. It uses 40 training, 200 first held-out and 200 second held-out episodes, and ends with `41 checks, 0 failed`. The chain of receipts for the stand-in policies has 36 lines and verifies. Held-out set 1 at cap 96, each cell passed over episodes:

| Stand-in policy | A | B | C | E | N |
|---|---|---|---|---|---|
| unchanged answer | 0/200 | 0/200 | 0/200 | 0/200 | 0/200 |
| recompute (exact) | 200/200 | 200/200 | 200/200 | 200/200 | 200/200 |
| oracle (tries one-step repairs from the amounts) | 0/200 | 0/200 | 188/200 | 86/200 | 0/200 |
| blind (moves one variable by the largest amount shown) | 0/200 | 0/200 | 89/200 | 32/200 | 0/200 |
| verbose (writes a long lead-in) | 0/200 | 0/200 | 0/200 | 0/200 | 0/200 |

The verbose policy breaks the format in all 200 replies in every text, and that is counted apart from a failed repair.

The dry run's 41 checks show that the exact checker, the sign test, the ratchet, the latch, the receipt chain and the budget guards each behave as designed. The table shows that the C, E and N texts separate a policy that reads the amounts from one that does not. The oracle scores 0 on N because its sign convention is written into the policy, and that is not a property of any model.

The test suite runs 346 tests (6 skipped without the tokenizer package) and passes. `mutate.py` removes 288 guards one at a time and every one is caught by a failing test. These too check the harness only.

The dry run also runs the whole registered procedure against a fake client twice. With a gain built in for C, the verdict is `support`, and the second held-out set is touched once. With no gain, the verdict is `cannot_test` and the second set is never touched. The fake pilot reports 200 calls and 8 steps. These are properties of the fake.

### Cost of the plan

`cost.py` prints the cost of the pilot and of the full plan, with every item. The totals are below. The rule count is the documented counting rule in `evaluate.py`. The tokenizer count uses the one carried by tml_renderers.

Prices are the rates published in the Tinker model table (https://tinker-docs.thinkingmachines.ai/tinker/models.json) for the 64K context, read on 2026-11-21: 0.75 dollars per million training tokens, 0.15 per million prefill tokens and 0.50 per million sampled tokens.

| Plan | Tokens (rule) | Dollars (rule) | Tokens (tokenizer) | Dollars (tokenizer) |
|---|---|---|---|---|
| Pilot, one adapter, 256 examples | 172,549 | 0.0864 | 184,306 | 0.0924 |
| Full plan, three texts, two seeds | 12,572,333 | 5.0406 | 13,385,972 | 5.3646 |

The exact full-plan cost with the tokenizer is 26823111/5000000 dollars. The plan sets a ceiling of 0.50 dollars for the pilot and 12.00 for the full run.

## Limits

- Nothing was run against the real service. The calls follow the installed library's signatures and are tested against fakes only. The order of calls, the time per sampling call and the step time are unmeasured.
- Whether the tokenizer carried by tml_renderers matches the Mini model is a guess. The chat layout matches the renderer id for id, but whether the service applies the same layout to a tuned model is not checked. The pilot is there to check it.
- Real billing rules are not verified. The cost table is arithmetic at published prices, and the sampling part is an upper bound. The forced opening moves two tokens per call from the training target to the prompt, so training tokens are unchanged and prefill grows by two tokens per call.
- The model card says minimum reasoning effort does not fully disable reasoning, and a local copy shows four switches that do not turn it off. The forced opening is the control. Whether the service accepts a prompt that ends with the opening is not checked, and the first pilot gate measures it.
- The pilot gate values (at most 5 percent of replies opening a block of their own, 20 percent format breaks, a pass rate between 5 and 95 percent, 12 hours projected) are choices and not measurements.
- The local baseline is one greedy run of a quantised copy on 50 episodes per cell. The renderer has no completion prompt that ends with the opening, so the layout test builds that comparison from its completion prompt plus the two opening ids.
- The gates are code that the same agent can edit. `ratchet.py`, `latch.py` and `driver.py` are not in the harness hash. The latch tokens live in memory, and the head of the receipt chain is pinned in memory unless it is kept elsewhere.
- Rescoring proves that recorded outcomes follow from recorded replies. Invented replies would pass it.
- The approvals file that allows a paid run belongs to the owner, in a place the agent cannot write. The code cannot enforce that.
- The chance floor on text E is exact for the first held-out set only.
- A small true effect is mostly missed. The plan's power table says which effects the design can see.

## Relation to the earlier experiment

The earlier experiment is the folder `repair-signal-2026-11-20`, which is in open pull request 38 of this repository and may not be on the default branch yet. It tested the same idea without training and did not support it. A separate open pull request, 42, audits that record's compute confound.

Its main confound was that one model escaped into long open reasoning, which the other arms could not use equally. The forced opening removes that route at the start of every reply, and the pilot counts replies that open a block later.

This record keeps the puzzle generator, the exact checker and the texts for A and B from that experiment, vendored in `vendor/rsig.py` with its SHA-256 pinned in `vendor/MANIFEST.json`. `vendor_loader.py` refuses to load it if the hash differs. The seed ranges here are disjoint from the earlier registered ranges.

## Research method followed

- One compute cap for every comparison. Every reply is capped at 96 answer tokens after the forced opening, for the untrained baseline and every adapter alike, and the ratchet refuses a comparison made at a different cap. A free-reasoning run is a different budget and is only a reference line.
- A locked harness. The evaluation code, episode builder, vendored generator and decision registry are pinned by hash in every receipt.
- Chained receipts without floats. Each line holds the hash of the line before it, and rates are stored as a numerator and a denominator.
- An unchanged candidate is rejected, by descriptor or by identical replies.
- A held-out set touched once. The second set is evaluated once per registered decision, and the touch is recorded before the evaluation starts.
- The checker is never trained into the model. The exact checker is the only judge, and training sees only its own feedback text.
- Exact claims use exact arithmetic (fractions), and the power table has a second checker that shares no code.
- A result against the claim, or a `cannot_test`, is reported with the same weight as one for it.

## Files

- `PREREG.md`: the plan, with its dated revision notes.
- `episodes.py`, `codec.py`, `evaluate.py`, `reference_policies.py`: episodes, token layout, the locked evaluation and the stand-in policies.
- `receipts.py`, `latch.py`, `ratchet.py`, `decisions.json`: the receipt chain, the once-only touch and the accept rule.
- `driver.py`, `tinker_backend.py`, `local_backend.py`, `fakes.py`: the run, the paid backend and test doubles. The paid backend refuses to start without an owner approval for the exact run id.
- `cost.py`, `power.py`, `dryrun.py`, `mutate.py`, `tests/`, `checks/`: the checks. `mutate.py` removes each guard by an exact text substitution and requires a test to fail.
- `vendor/`: the pinned generator and checker.
- `local-baseline/`: the free local measurement of the untrained model on pilot evaluation seeds, with its script, data and README.

## Disclosure

The code, tests and plan were written and run by AI agent sessions under the direction of the research team's human owner, with independent review rounds by other agent sessions. The plan went through two such reviews before registration, and the revision notes in `PREREG.md` list what they changed.

The fixes made after the second review, 18 files changed and two check scripts added, have not been reviewed by a second agent. No human has line-reviewed the code. No paid service was called.
