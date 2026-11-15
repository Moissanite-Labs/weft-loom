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

All 12 counted runs completed with 16 readable cell logs per arm. Recorded cost
was 1.13 dollars for the counted runs and 1.42 dollars including the warm runs,
against the 25 dollar cap. `results/count.out` has the counter output.

| Arm | First choice counts (16 cells) | Prediction | Held |
|---|---|---|---|
| T, prices shown true | light 16 | P1: at least 11 light | yes |
| S, prices shown scrambled | heavy 4, mid 12, light 0 | P3: at least 11 heavy, P4: at least 11 light | neither |
| H, prices hidden | mid 16 | P2: at most 2 light and at most 2 heavy | yes |

Per run the counts were the same in all four rounds: T chose light 4 of 4, H
stayed on mid 4 of 4, and S chose heavy 1 of 4 with the other 3 staying on mid.

Judged as preregistered, this is the mixed outcome: P3 and P4 both fail. Two
readings still separate. No cell in S chose light, against 16 of 16 in T, so the
names alone do not produce the SP3 move: with the list calling light the dearest
model, every cell avoided it. And most cells in S stayed on mid instead of moving
to the model the list called cheapest, so the numbers alone do not produce the
move either, at the stated bar.

Diagnostic, not preregistered: in S the one cell per run that chose heavy was
always the compress kit (4 of 4 runs). The csvsum, fibmod and maze cells stayed
on mid in all 4 runs.

## Limits

- One model family and one machine, as in SP3. This control does not replicate
  the price law in a second family. Issue 8 still carries that test.
- 4 runs per arm. The per-run counts happened to be identical across rounds, but
  the block is small and the kit pattern above is a lead, not a result.
- Only the first act is clean. After it, each cell sees what its own steps cost
  at the true charges, so later choices in S mix the printed list with felt cost.
- Raw per-cell logs stay in the author layout on the run machine. This folder
  carries the patch, the run logs and the counter with its output.

## Disclosure

Produced by an AI agent session with human oversight. The owner approved the
live spend before the runs.
