# Repair-signal training loop, design and dry run (2026-11-21)

## Question

When a model must repair a rejected answer to a rational difference-constraint puzzle, and may answer only with the repaired assignment under one small token cap, does training on feedback that gives the exact amount of each violation let it repair more often than training on feedback that names only the violated constraints?

The record holds the preregistered plan and the training loop that would run it on Inkling 2 Mini through the Tinker service, with a harness that is built and tested but has not been used on any model. 

Every prompt that is sampled from ends with the model's turn already opened for an answer (the forced opening), because the untrained model opened a thinking block in every local call that left the opening to it, and none of the four switches tried turned that off.

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

`python3 -I -B local-baseline/check_seeds.py` checks that the committed local baseline holds pilot evaluation seeds only. `python3 -I -B local-baseline/facts.py` prints the free-reasoning counts, the time per call and what it projects for the full plan, and the smoke-run facts (output in `local-baseline/facts.txt`).

`cost.py --venv-python PATH` counts with the real tokenizer through a worker that imports tml_renderers. The layout test in `tests/test_layout_real.py` also needs that package and is skipped without it (7 tests). The layout test and the tokenizer cost count were run with a Python that has the package, and all 7 layout tests passed.

Two more tests need the service library or the tokenizer package: the conformance test in `tests/test_api_check.py` and the real-tokenizer cost test in `tests/test_pilot_cli.py`. Both passed with that Python, and are skipped without it.

The outputs are committed under `data/`: `dryrun.txt` (`dryrun.py`), `cost-rule.txt` (`cost.py`), `cost-tokenizer.txt` (`cost.py --venv-python PATH`, with a Python that has tml_renderers), `targets.txt`, `e_floor.txt`, `rule2_ties.txt`, `power-400.txt` (the script of the same name, run as listed above) and `tinker-api-check.txt` (`checks/tinker_api_check.py`, run with a Python that has the service library).

The dry run is deterministic and runs on any machine. It was run here on one Apple laptop with the system Python.

## How to run the pilot

The owner approves the pilot (one adapter trained on text C with 256 examples, the untrained model and the adapter each sampled on the 100 pilot evaluation puzzles, ceiling 0.50 dollars) and starts it. The steps:

1. Print the approval row for a new run id. This prints one line and does nothing else.

```
python3 -I -B pilot_cli.py --run-id PILOT-RUN-ID --print-approval-row
```

The row names the run id, the plan `pilot`, the plan's fingerprint and the ceiling "0.50".

2. The owner puts that row in the `approvals` list of an approvals file, as `{"approvals": [ROW]}`. The file lives outside this repository, in a place the agent cannot write. The spend ledger and its lock file are written beside it.

3. In the shell that will run the command, set `TINKER_API_KEY` to the service key. The runner takes the key only from that variable. It refuses to start when the variable is empty, so the library cannot fall back to a stored credentials file. It never prints or writes the variable.

   The runner registers the variable's value with the backend. Every error text, even one raised inside a service call, loses that exact value first, whatever characters it holds, and then goes through the `redact` pattern and its 400-character cut.

4. Run the pilot from this folder with a Python that has the service library and `tml_renderers`, and a new or empty output directory.

```
PATH-TO-VENV-PYTHON -I -B pilot_cli.py --approvals PATH-TO-APPROVALS --run-id PILOT-RUN-ID --out NEW-OUTPUT-DIR
```

The runner checks the approval, the plan, the ceiling and the lock, and prints the planned cost and the ceiling. Only then does it build the service client. The pilot trains one adapter, samples the base model and the adapter on training-range seeds only, and projects the time of the full plan from what it measured.

5. Read what comes out in the output directory.

| File | Content |
|---|---|
| `pilot-result.json` | integers and strings only: every measurement, every gate as the string "true" or "false", the go verdict, counts by outcome for the base model and the adapter, tokens and exact dollars by kind from the spend ledger, and the time per training step and per sampling call as integer nanosecond totals with their counts |
| `replies.jsonl` | one line per call that reached the service, written as the call ends: which model, tier, seed, the decoded reply, the outcome, and `returned`, the token ids of every sequence exactly as the service returned them, with `returned_tokens` their count. A paid call that then raised (an overrun, a wrong number of sequences) has a row with status `raised` and an empty outcome. A call that failed inside the service before any answer has `returned` null |
| `receipts.jsonl` | the chain of receipts, with the stored replies and the harness lock beside it |
| `pilot-summary.md` | a short table for a person |

A finished pilot exits 0, whether the gates give a go or a no-go.

If an error stops the run after it has started, the runner still writes what it has, marks `pilot-result.json` as `incomplete` with the redacted error text, and exits 1. SIGINT, SIGTERM and SIGHUP give the same result with the error `interrupted`.

A refusal before the start (no approval row, wrong plan, a ceiling too low or above 0.50, a used output directory, no key) exits 2 and writes no file. The output directory is made only after the run has started. `--fake` runs the same code path against `fakes.py`, with no key and no network, and the tests use it.

Before the first real run, run the conformance check of the backend against the installed library (it builds no client and needs no key). It prints one line per call and exits 1 on a mismatch. `--old-scripts` names the earlier scripts the backend was adapted from, to list each call they make differently.

```
PATH-TO-VENV-PYTHON -I checks/tinker_api_check.py --old-scripts EARLIER-SCRIPT-1 EARLIER-SCRIPT-2
```

Its output for the installed library is `data/tinker-api-check.txt`. It found two mismatches in the backend, now fixed: `create_lora_training_client` and `create_sampling_client` return a future of the client in tinker 0.39.0, and the backend used that future as the client. The fake client now returns futures too, and takes the same argument names as the library.

## Results

None yet. No model has produced a result for this question.

The dry run checks the harness with stand-in policies. It says nothing about any model. It uses 40 training, 200 first held-out and 200 second held-out episodes, and ends with `44 checks, 0 failed`. The chain of receipts for the stand-in policies has 36 lines and verifies. Held-out set 1 at cap 96, each cell passed over episodes:

| Stand-in policy | A | B | C | E | N |
|---|---|---|---|---|---|
| unchanged answer | 0/200 | 0/200 | 0/200 | 0/200 | 0/200 |
| recompute (exact) | 200/200 | 200/200 | 200/200 | 200/200 | 200/200 |
| oracle (tries one-step repairs from the amounts) | 0/200 | 0/200 | 188/200 | 86/200 | 0/200 |
| blind (moves one variable by the largest amount shown) | 0/200 | 0/200 | 89/200 | 32/200 | 0/200 |
| verbose (writes a long lead-in) | 0/200 | 0/200 | 0/200 | 0/200 | 0/200 |

The verbose policy breaks the format in all 200 replies in every text, and that is counted apart from a failed repair.

The dry run's 44 checks show that the exact checker, the sign test, the ratchet, the latch, the receipt chain and the budget guards each behave as designed. The table shows that the C, E and N texts separate a policy that reads the amounts from one that does not. The oracle scores 0 on N because its sign convention is written into the policy, and that is not a property of any model.

The test suite runs 429 tests (9 skipped without the service library and the tokenizer package) and passes. `mutate.py` removes 339 guards one at a time and every one is caught by a failing test. These too check the harness only.

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

- Nothing was run against the real service. The calls are compared with the installed library's signatures by `checks/tinker_api_check.py`, and the logic is tested against fakes only.
- The sampling calls, the checkpoint save and the base sampler have no earlier run against the real service behind them, because neither earlier script makes them. Whether the service accepts greedy sampling (temperature 0.0) with integer stop ids for this model cannot be settled from the installed code. The order of calls, the time per sampling call and the step time are unmeasured.
- Whether the tokenizer carried by tml_renderers matches the Mini model is a guess. The chat layout matches the renderer id for id, but whether the service applies the same layout to a tuned model is not checked. The pilot is there to check it.
- Real billing rules are not verified. The cost table is arithmetic at published prices, and the sampling part is an upper bound. The forced opening moves two tokens per call from the training target to the prompt, so training tokens are unchanged and prefill grows by two tokens per call.
- The model card says minimum reasoning effort does not fully disable reasoning, and a local copy shows four switches that do not turn it off. The forced opening is the control. Whether the service accepts a prompt that ends with the opening is not checked, and a refused opening would stop the pilot with an error.
- The pilot gate values (at most 5 percent of replies opening a block of their own, 20 percent format breaks, a pass rate between 5 and 95 percent, 12 hours projected) are choices and not measurements.
- The local baseline is one greedy run of a quantised copy on 50 episodes per cell. The renderer has no completion prompt that ends with the opening, so the layout test builds that comparison from its completion prompt plus the two opening ids.
- The gates are code that the same agent can edit. `ratchet.py`, `latch.py` and `driver.py` are not in the harness hash. The latch tokens live in memory, and the head of the receipt chain is pinned in memory unless it is kept elsewhere.
- Rescoring proves that recorded outcomes follow from recorded replies. Invented replies would pass it.
- The full run does not check that a pilot gave a go. The go is the owner's call and the full run must not start after a no-go (PREREG.md, "After the pilot"). At the local speed the time gate would fail, and the service's speed is unknown.
- The service library retries requests itself (10 retries by default, and a request can wait up to 120 minutes without progress), and the meter cannot see these. A retried request that the server already served could be billed twice, and a stuck request can hold the run for hours. The runner does not change these settings. After the run, compare the spend in the service console with the ledger's total.
- A service that returns more tokens than asked for stops the run at the first such reply, after that reply is counted in full. The overshoot is that one reply's excess, which has no upper limit.
- The run lock is `flock`, so it works on macOS and Linux only, and it covers one ledger file: two copies of the approvals file in two places make two ledgers. An overrun followed by a crash before its ledger line is written loses those extra tokens from the ledger.
- The mark that tells `run_registered` a run's token counts came from `start_run` is set in ordinary code that the same agent can edit.
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
- `pilot_cli.py`: the command line runner of the pilot (see "How to run the pilot"). It refuses a used output directory, a missing key and any approval that is not the pilot's, logs every raw reply, and writes the result file with integers and strings only.
- `driver.py`, `tinker_backend.py`, `fakes.py`: the run, the paid backend and test doubles. The paid backend refuses to start without an owner approval for the exact run id and the exact plan, and it holds a lock so that only one process uses a ledger at a time. The only sampling path is the paid backend's responder, which builds every prompt with `codec.py`, forced opening included.
- `checks/tinker_api_check.py`: the static comparison of the backend with the installed service library.
- `cost.py`, `power.py`, `dryrun.py`, `mutate.py`, `tests/`, `checks/`: the checks. `mutate.py` removes each guard by an exact text substitution and requires a test to fail.
- `vendor/`: the pinned generator and checker.
- `local-baseline/`: the free local measurement of the untrained model on pilot evaluation seeds, with its script, data, README, the sanitized smoke and run logs under `logs/`, and `facts.py` with its output `facts.txt`, which print the numbers the plan quotes from them.

## Disclosure

The code, tests and plan were written and run by AI agent sessions under the direction of the research team's human owner, with independent review rounds by other agent sessions. The plan went through two such reviews before registration, and the revision notes in `PREREG.md` list what they changed.

A third independent review found seven points to fix and four small ones. The fixes made for it (the run lock and plan binding in the backend, the single decision procedure, the removal of the old local responder, the committed logs and the rewording of the local section) have not been reviewed by a second agent. No human has line-reviewed the code. No paid service was called.
