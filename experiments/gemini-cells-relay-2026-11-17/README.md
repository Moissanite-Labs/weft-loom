# Gemini-cells relay, 2026-11-17

## Question

Weft-loom pull request 27 proposes twin cells that take turns editing each other's harness. Does that end with better harnesses than two cells that each edit their own harness under the same referee, and does a cell given a better harness build better than a cell left in the seed?

## Status

`design`

The instrument is here, tested offline and calibrated live. No relay run has been made yet, apart from one excluded warm run. The plan is committed, and the runs follow in later commits.

## Preregistration

[PREREG.md](PREREG.md), committed and pushed before the first relay run, with the hash of every frozen file.

## What is here

| Path | What it holds |
|---|---|
| `seed/` | The seed harness every cell starts from: a loop, a prompt and two tool files. The only code a cell may change |
| `referee/sandbox.py` | Runs cell code with no network, no credentials and one writable folder |
| `referee/brain.py`, `referee/cellapi.py` | The capped, logged line from a cell to its model, and the spend ledger |
| `referee/bench.py` | Episodes, benchmarks, harness snapshots stored by hash, and build turns |
| `referee/relay.py` | The turn loop, the gate and the five arms |
| `run.py`, `analyze.py` | Commands for calibration, runs and tables |
| `calibration/ref-harness/` | A harness written by the lead, used only to check that the benchmark can tell a better harness from the seed |
| `tests/` | Twelve offline tests of the relay with a scripted model, and the sandbox self-test |
| `results/sandbox_selftest.out` | Output of the sandbox self-test: 26 of 26 checks |

## How to rerun

The offline checks need root on Linux and no model:

```
cd experiments/gemini-cells-relay-2026-11-17
python3 -m unittest tests.test_offline
python3 tests/sandbox_selftest.py
```

## Results

None yet.

## Limits

- Nothing has been run against a model beyond a boot check and a throwaway smoke task.
- The model is reached through the `claude` command line tool, which adds notes of its own to every call. `referee/brain.py` says what is done about that.

## Disclosure

Written by an AI agent session after the owner handed the programme over on 2026-11-17. A second agent session is writing the task families.
