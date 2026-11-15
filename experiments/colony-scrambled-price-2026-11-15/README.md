# Colony scrambled-price control, 2026-11-15

## Question

SP3 in `experiments/razi-cells-laws-2026-11` found that cells shown a price list
move to the cheapest model at their first act. The model names (`light`, `mid`,
`heavy`) are visible in every arm, so the result does not say whether the cells
read the numbers or follow the names. Do they still move to the model the list
calls cheapest when the numbers for `light` and `heavy` are swapped?

## Status

`pilot`

## Preregistration

[PREREG.md](PREREG.md), committed and pushed before any run in this record. The
scramble patch, the run script and the counting script are in this folder with
their hashes in the preregistration.

## What is here

| File | What it holds |
|---|---|
| [PREREG.md](PREREG.md) | Design, predictions with pass marks, spend cap, frozen file hashes |
| `metab-scramble.patch` | The display-only change to the cells harness: `CELL_PRICE_SCRAMBLE=1` swaps the printed prices of `light` and `heavy`. Charges are unchanged |
| `run_scrambled.sh` | Runs the three arms in the fixed order, warm runs excluded |
| `count_first_choice.py` | Counts first model choices from the cell logs and checks each log's arm row |
| `results/` | Counter output and run logs, added after the runs |

## Results

Added after the runs, against the predictions as written.

## Disclosure

Produced by an AI agent session with human oversight. The owner approved the
live spend before the runs.
