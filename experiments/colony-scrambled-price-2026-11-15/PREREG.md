# Preregistration: scrambled-price control for the colony price law

Written 2026-11-15, before any run in this record. Follows weft-loom issues 8 and 12.
The live spend was approved by the owner on 2026-11-15 with the run count and cap below.

## Question

In SP3 of `experiments/razi-cells-laws-2026-11`, cells shown a price list chose the
cheapest model (named `light`) at their first act, and cells not shown it did not move.
The model names appear in both arms, so that result does not separate reading the
numbers from following the names. This control separates them.

## Design

Same harness, task set and settings as SP3 arms a and b: the flat shape with 4 kits
(`needs4k.json`), 400 energy at birth, every cell born on `mid`, sense measured in
every arm and shown in none. Three arms:

- **T**: price list shown, numbers true.
- **S**: price list shown, the numbers for `light` and `heavy` swapped, so the list
  calls `heavy` the cheapest model and `light` the dearest. Charges are unchanged:
  `price()` still prices every step, and only the printed menu uses `shown_price()`.
  The patch is `metab-scramble.patch` in this folder.
- **H**: price list hidden. Cost is felt only, as in SP3 arm b.

4 runs per arm, 4 cells per run, 16 cells per arm. One warm run per arm first
(`scwT`, `scwS`, `scwH`), excluded from every count. Counted runs run in the order
T, S, H, four rounds, one run at a time (`run_scrambled.sh`).

Menu (router catalog on this machine, energy units per 1000 tokens): light 1/5,
mid 20/100, heavy 40/200. Under the scramble the list prints light 40/200, mid
20/100, heavy 1/5. That was checked offline before this file was committed, and
`kit_selftest.py` passes with the patch in place.

## Measure

The first model choice of each cell: the model named for the next step in the
cell's first act, counted by `count_first_choice.py` in this folder. The counter
checks each cell's `laws` row against its arm and fails if they disagree. A run
with fewer than 4 readable cell logs is reported as it stands and is not replaced.

## Predictions

- **P1 (T)**: at least 11 of 16 first choices are `light`.
- **P2 (H)**: at most 2 of 16 first choices are `light`, and at most 2 are `heavy`.
- **P3 (S, numbers are read)**: at least 11 of 16 first choices are `heavy`, the
  model the scrambled list calls cheapest.
- **P4 (S, names are followed)**: at least 11 of 16 first choices are `light`.

Reading of the result, fixed here: P3 holding means the cells read the numbers.
P4 holding means the SP3 effect is a naming effect. Neither holding (choices split,
or cells mostly stay on `mid`) is a mixed result and will be recorded as one.
P1 or P2 failing means this block does not reproduce SP3, and the S arm is then
read only against this block's own T and H arms.

Secondary, with no pass mark: recorded dollar cost per arm from the step usage rows.

## Spend

15 runs in total (3 warm, 12 counted), one model family (the Anthropic menu in
`metab.py`). Hard cap 25 dollars of recorded cost across all runs in this record,
warm runs included. SP3 run logs put one run between about 0.03 and 1 dollar, so
the expected total is under 5 dollars. If the cap is reached the block stops and
the record says so.

## Files as frozen

```
be8a9e6175b4d34d5254ac3522455da0ef5cea8b6163a2d8ce6067a733ad05df  metab.py (with the scramble patch)
d38c5eb291fe9e21d8823aaa14a785d7edb650c242ab6d5c3e74ee85b1c71ca6  colony.py
27b65154c66bb80a27317f8cff9b77141e779f44ec52fe4e65c1d4131b490f08  run_metab.sh
460851ccb5d55a2a7a159dc7aba11578e8f13f51989844d6c8765d889a0c81f3  needs4k.json
f1db57d08e3a3fb15d6fe32d816c1bffb6d72b638007e530905b2fb75a98936c  run_scrambled.sh (this folder)
367e7a6640b924593b8c79bb944934e8902fbef19ca91ac95d59fbc3d90f5116  count_first_choice.py (this folder)
e939cb9a33209afc4102ac3b129bf5175f566ee577a5578ee5cc361a473cb8f0  metab-scramble.patch (this folder)
```

The harness lives in the author layout on this machine (`Work/razi-tools/cells`,
`Work/razi-cells/exp`, Exo at `Work/exo-live`), as the laws record describes. The
patch file and the hashes above are what this record can carry of it.

## Disclosure

Written and run by an AI agent session with human oversight. The owner approved
the spend, the run count and the cap before the runs.
