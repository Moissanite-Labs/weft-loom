# Local baseline of the untrained model (exploratory, free)

This folder holds a measurement of the untrained Inkling 2 Mini on the pilot evaluation episodes of the training-loop record. It ran on one Apple laptop with a quantised local copy of the model, at no cost. It does not use the paid service and says nothing about any trained adapter.

## What it is

One greedy run (temperature 0, top_k 1) of the untrained model with a quantised copy (Q8_0, llama.cpp tag b12613). It was run on the pilot evaluation seeds only, tier S 310000 to 310049 and tier M 360000 to 360049, which are training-range seeds and never a held-out set.

Mode F forced the answer block: the prompt ends with the model's turn opened for an answer, and the reply cap is 96 answer tokens. It covers texts A, B, C, E and N, 50 episodes per tier and text, 500 calls. Mode R let the model reason freely for up to 2000 tokens, on texts B and C, the first 15 episodes of each tier, 60 calls. Mode R was stopped at its time budget of 70 minutes.

The results are quoted, with what they do and do not show, in the section "What the local model did" of [PREREG.md](../PREREG.md). Reply scoring uses the record's own exact checker.

## Files

- `baseline.py`: the script that ran it. It needs a llama.cpp server binary and a GGUF file of the model, given as `--llama-server` and `--model`. It reads the record's `codec.py`, `episodes.py` and `evaluate.py` from `--record` (default: the folder above) and writes to `--out` (default: this folder).
- `results.jsonl`: one line per call, 560 lines, 110 KB. Each line holds the text, tier, seed, mode, the reply, generated tokens, the stop reason, seconds and the outcome.
- `summary.json`: counts per mode, text and tier, the paired count of C against B and the seconds per call.
- `check_seeds.py`: the check below.

## Pilot seeds only

`python3 -I -B check_seeds.py` reads every line of `results.jsonl` and fails if a tier is not S or M or if a seed lies outside its pilot evaluation range. It also checks that the counts in `summary.json` follow from the lines. On the committed files it prints `560 lines, 100 distinct (tier, seed) pairs, 0 outside the pilot evaluation ranges` and exits 0. `tests/test_local_baseline.py` runs it, and also runs it on files that hold a bad seed, which it must refuse.

## What was changed after the run

The paths of the local machine were replaced by command-line options, the layout check was pointed at the forced-opening prompt of the record's current `codec.py`, and a `controls` mode that starts no server was added. The measured run used the same prompt text. The edited script was not run again, because that needs the model server. The offline `controls` mode was run and passes.

## Limits

- The text layout was built locally and may differ from the one the paid service applies. The token ids matched `codec.py` on 15 prompts through this copy's tokenizer.
- A quantised copy can answer differently from the service's model.
- One greedy run with 50 episodes per cell. A cell's pass rate is only known to within about 14 points.
- Prompt caching was on, and calls were stopped at the end marker or at the end of the first answer block.
