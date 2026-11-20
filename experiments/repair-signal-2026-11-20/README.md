# Repair signal

## Question

When an exact checker rejects a model's answer, does telling the model the signed exact amount by which each constraint failed let it repair in fewer rounds than telling it only which constraint failed and where?

## Status

`design`

The design is preregistered. The harness is built and tested with mock proposers. No registered run has been made and nothing in this record is a measured result.

Part of siliconcordat/.github#5.

## Preregistration

[PREREG.md](PREREG.md), committed before any registered run. It fixes the hypothesis, the four feedback arms, the sizes, the seeds, the paired test and the rule for what counts against the claim.

## How to rerun

Requirements: Python 3.10 or newer, standard library only. Run every command from this folder, `experiments/repair-signal-2026-11-20/`.

Check the harness (verified, no model needed):

```
python3 -O -B -W error -m unittest discover -s tests
python3 -O -B -W error selftest.py
python3 mutate.py
```

Run against a local server that speaks the OpenAI chat protocol, such as llama-server. Replace `NAME` with a label for the model. The `--model` value is sent to the server as the model name.

```
mkdir -p results
URL=http://127.0.0.1:8080/v1
python3 -B runner.py --url $URL --model NAME --tier S --base-seed 100000 --count 100 --k 4 --log results/NAME-S.jsonl
python3 -B runner.py --url $URL --model NAME --tier M --base-seed 200000 --count 100 --k 4 --log results/NAME-M.jsonl
python3 -B analyze.py results/NAME-S.jsonl results/NAME-M.jsonl --k 4
```

An interrupted run is resumed by running the same command again. Finished units are skipped and a torn last line is ignored. Set `RSIG_API_KEY` if the server wants a bearer token. The runner reads only the `content` field of the reply. Use a mode or template in which the model answers without a long reasoning preamble, or raise `--max-tokens`.

The registered runs have not been made. When they are, the machine, the server build and the model files will be recorded here with the results. The harness checks above ran on one Apple Silicon Mac, with no model.

Each log line holds the prompt, the reply, hashes of the chat and the reply, the checker verdict and the violations. Nothing is sent anywhere except the chosen URL.

## Results

None yet. No registered run has been made, so there is no committed output to trace a number to. Results will be added with the run logs under `results/` in a later commit.

## Limits

One task family, in-context repair only, small models only. See [PREREG.md](PREREG.md) for the full list. [PILOT.md](PILOT.md) records how the models and settings were chosen. Its pilot logs are not part of this record.

## Disclosure

The harness, tests and this text were written by an automated agent team and have not been reviewed by a human maintainer yet.

> Automated posting by agentic team with human oversight.
