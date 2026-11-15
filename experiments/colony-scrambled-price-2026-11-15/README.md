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
| `extract_steps.py` | Writes `results/steps.jsonl` from the cell logs: the arm row, one row per paid step, one row per act with the model it sets for the next step, and the downshift, bad-reply and death rows. It keeps no shell output and no reply text |
| `recount.py` | A second count, written apart from the first, that reads `results/steps.jsonl`. It adds how each cell first came to run on `light` |
| `results/` | Counter output and run logs, added after the runs. The per-step extract, the hash of each cell log and the recount output, added after review |

## How to rerun

The counts can be redone from this folder with any Python 3, from the root of a
checkout. The output should match `results/recount.out`.

```
python3 experiments/colony-scrambled-price-2026-11-15/recount.py
```

The runs were live calls to hosted models and are not seeded, so running them
again gives a new sample and costs money. They were made on one Apple Silicon
Mac on 2026-11-15, between 19:06 and 19:22 UTC, with the harness at the hashes in
the preregistration. On that layout the commands are:

```
sh run_scrambled.sh warm
sh run_scrambled.sh full
python3 count_first_choice.py
python3 extract_steps.py
```

`run_scrambled.sh` changes to the harness folder itself and writes its run logs
there. The two Python scripts read the cell logs from that folder unless they
are given another.

## Results

All 12 counted runs completed with 16 readable cell logs per arm. Recorded cost
was 1.13 dollars for the counted runs and 1.42 dollars including the warm runs,
against the 25 dollar cap. `results/count.out` has the counter output, and
`results/recount.out` a second count that agrees with it.

| Arm | First choice counts (16 cells) | Prediction | Held |
|---|---|---|---|
| T, prices shown true | light 16 | P1: at least 11 light | yes |
| S, prices shown scrambled | heavy 4, mid 12, light 0 | P3: at least 11 heavy, P4: at least 11 light | neither |
| H, prices hidden | mid 16 | P2: at most 2 light and at most 2 heavy | yes |

Per run the counts were the same in all four rounds: T chose light 4 of 4, H
stayed on mid 4 of 4, and S chose heavy 1 of 4 with the other 3 staying on mid.

Judged as preregistered, this is the mixed outcome: P3 and P4 both fail. Two
readings still separate. No cell in S chose light at its first act, against 16
of 16 in T, so the names alone do not produce the SP3 move. The arm with no list
also has 0 of 16 on light there. And most cells in S stayed on mid instead of
moving to the model the list called cheapest, so the numbers alone do not
produce the move either, at the stated bar.

Diagnostic, not preregistered: in S the one cell per run that chose heavy was
always the compress kit (4 of 4 runs). The csvsum, fibmod and maze cells stayed
on mid in all 4 runs. The 16 cells of an arm are 4 kits by 4 runs, and within
each kit all 4 runs made the same first choice in every arm, so an arm holds
about 4 independent outcomes.

### After the first act

Not preregistered, and added after review. The first act is at step 0 in all 48
cells. When a cell cannot pay for a step on its model, the harness moves it down
a model and logs a `downshift` row. The table says how each cell first came to
run on light.

| Arm | Chose light at the first act | Chose light at a later act | Put on light by a harness downshift | Never on light |
|---|---|---|---|---|
| T | 16 | 0 | 0 | 0 |
| S | 0 | 2 | 10 | 4 |
| H | 0 | 3 | 8 | 5 |

- With the true list every cell moved to light by its own act at once. With the
  scrambled list or with none, no cell did at its first act, and 2 and 3 of 16
  did at a later act before the harness moved them. The cells the harness moved
  had taken two to five acts without choosing light.
- The four compress cells in S were charged 200 to 226 for their first heavy
  step, against 26 to 45 for their first step on mid. None left heavy by its own
  act, though each took only one act while on heavy. The harness downshifted
  three to mid and then to light, and the fourth died after a second heavy step.
- Bad replies and deaths were not a preregistered measure. They occur only in
  the two arms that spent more. Bad replies: T 0, S 14, H 4. Cells that died:
  T 0, S 8, H 4. Recorded cost: T 0.10, S 0.53, H 0.49 dollars.

## Limits

- One model family and one machine, as in SP3. This control does not replicate
  the price law in a second family. Issue 8 still carries that test.
- 4 runs per arm. The per-run counts happened to be identical across rounds, but
  the block is small and the kit pattern above is a lead, not a result.
- Only the first act is clean. After it, each cell sees what its own steps cost
  at the true charges, so later choices in S mix the printed list with felt cost.
  The counts after the first act describe the runs and carry no pass mark.
- The full per-cell logs stay on the run machine, because they hold shell output
  from that machine. `results/steps.jsonl` carries the rows the counts need, and
  `results/raw_logs.sha256` the hash of each log.
- The harness on the run machine differs by one logging line from the copy in
  `experiments/razi-cells-laws-2026-11/code/cells/metab.py`. The patch applied to
  that copy does not give the hash in the preregistration, which is the hash of
  the file the runs used.

## Disclosure

Produced by an AI agent session with human oversight. The owner approved the
live spend before the runs. A second agent session reviewed the record, redid
the counts and added the extract, the rerun section and the counts after the
first act.
