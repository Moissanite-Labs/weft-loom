# razi-cells: start here (2026-11-10)

Read this, then `CONSULT-2026-11-10.md` and `TESTS.md`. Older handoff and report v1 are in `exp/archive/`.
Tensor-layer twin of L2: `APPLE-SILICON-DISSIPATIVE-SWARM.md` (weft PR #120). The Weismann gate ended coasting in the tensor swarm (0 of 256 idle cells) and cost 27% of error reduction. Watch for the same trade in L2.
Harness and provider work is out of scope for this research thread. It lives in Exo issues and PRs.

## What this is
Stem cells start from a NEED and an empty folder, write their own tools, and split (A/B) to test changes.
A local assay scores each version. A change is kept only if it beats the incumbent (`beats` rule in cell.py).
This is the agent-level twin of Weft Paper 1 (Moissanite-Labs/weft). Goal: test every report-3 variable,
with full scientific method, before writing the razi-cells paper.

## A's rules for this work
- Top priority project, budget unlimited. Waste is the problem, not spend.
- Cost ladder, cheapest first: hy4, sonnet 5.5, gpt-6.1-sol, opus 5.5, astra, mistral large 4, argon, fable.
  Use it to choose, not to always pick the cheapest. Comparing models has research value.
- OpenAI models use provider `openai`, never `chatgpt`. Anthropic models use `anthropic`.
- Apply obvious improvements without asking. Full agency on design.
- Every costly run: preregistered question in TESTS.md, usage logging, token budget, cheap pilot first.
- Judge hypotheses exactly as written. Numbers come from scripts, not eyes. Medians, paired by task.
- Never print or store keys. Cells have no network and no key.
- Nothing goes public without A. Weft repo is in stealth.

## Results so far (details in TESTS.md)
- Scaling the colony up (g4) halved wins per 100 calls. No brute-force scaling.
- Fable 5.1 and Argon: same improvement rate (10.53 vs 11.42 per 100 calls, t = 0.48).
- E08 (Argon): removing the `variants` tool raised median final_gain 6.0 -> 11.5 (artifact cells dropped,
  was 4.2). Not established: one ctrl run, two sided p 0.20. Bold proposals won 27 of 33.
- E09 (Argon, partial): a prompt nudge toward `try` changed nothing. Tool design beats instruction.
- E10 (Fable 5.2 vs 5.1 x ctrl vs novar, 2 reps): analysed, see TESTS.md. H8 rejected (5.2 did not gain
  more than 5.1 in ctrl: 1.045 vs 2.885). H9 rejected: removing `variants` helped 5.2 (2.387 vs 1.045) and
  hurt 5.1 (0.024 vs 2.885). The attractor effect is model dependent, not general. H10 held.
- Scoring artifact (fixed 2026-11-10): stderr was parsed for the score, so "OMP: Warning #179" scored 179.0.
  Touches b5, e8c1, e8s3, g3, g4 and 5 E10 cells. E08 needs a second analysis with those cells dropped.

- E11 (Sonnet 5.5, cheap protocol, 4 reps): ctrl beat novar, 0 of 4 tasks positive, p 0.0038. But novar
  cells stopped right after the assay, so the result mixed "variants finds better code" with "variants keeps
  cells working".
- E12 (Sonnet 5.5, 2x2 with a hold that refuses `done` until one improvement attempt): the hold raised
  attempts in novar from 1 of 16 cells to 15 of 16. With engagement equal, `variants` still has the higher
  median, not significant at 0.05. H19 and H21 failed as written, both decided by the maze task.
- Instrument fault found in E12: the maze task is invalid in E11 and E12. Cells make their own maze, most are
  unsolvable (answer -1), and some cells changed the input after the assay. Maze is reported, not used.
- Mistral Large 4 is usable as `custom-mistral:mistral-large-4` (unpriced route, compare on tokens).

## State on 2026-11-10 (read this before the older list below)
- The colony runtime is now `metab.py` (energy laws, kits owned by the harness). Results after E13 are in TESTS.md:
  mp1 to mp3, GR1 to GR4 (toy numpy growth), SP1, SP2, SP3, and the T-J3 adapter pilot.
- SP3 (price list shown or hidden, sense number shown or hidden, 16 runs): 6 of 12 guesses held. The cheap first
  choice is read off the price list. The sense number with the list shown was the best arm. Hand rewrites are not
  paid by the laws (IDEAS K23), which is the first thing to fix. Leads only: one model family, 4 runs per arm.
- T-J3 (LoRA genome on Inkling 2 Small through Tinker): pilot done, full run is seeds 0, 1, 2 into
  `tj3/tj3_s{0,1,2}.json`, judged by `adapters/tj3_report.py`.
- Next steps are IDEAS T-K4. The map of open directions is `map/MAP.html`.

## State on 2026-11-10, later (L1)

- A handed the direction over. The path chosen: heredity. See IDEAS.md section L and TESTS.md "L1".
- New code: `lineage.py` (driver), `lineage_report.py` (report, run unchanged), `tests/lineage_offline.py`,
  `run_l1.sh pilot|full`. `metab.py` has opt-in `CELL_PAY_ANY`, `CELL_GERM`, `CELL_LINEAGE`.
- T-J3 is parked: the plain arm did not beat the base rate and the vendor's free checkpoint limit stopped arm gn.
- After the L1 run: copy final germlines are in `results/l1-final/<run>/<kit>`, score them with `refscore.py`,
  then run `lineage_report.py REF.json h=l1h1,l1h2,l1h3 b=l1b1,l1b2,l1b3`.

## Next (older list, items 1 and 4 partly done)
1. Harness-owned kit per need (IDEAS G2): fixed inputs, correctness check and timing command owned by the
   harness, read-only to the cell, final score measured by the harness. No new experiment before this.
2. Mixed-model colony: strong model for tool-building steps, cheap model for routine steps,
   vs all-cheap and all-strong. Outcome: final_gain and tokens per improvement. Pilot 1 task first.
3. Report-3 variables still untested: apoptosis plus re-clone, elastic resistance near protected
   files, mutation rate tied to failing tests, fast reflex tier, pre-gate on model calls.
   Corpus ideas not built: s-expression genomes, consolidation dial, self-evaluator.

4. Section G of IDEAS.md (from A's Google AI Mode conversation): score by Bend interaction count (G1),
   lambda evaluator task (G3), Lean arm against Bend arm (G5). First pilot: can models write valid Bend at all.
5. Source context: `sources/siliconcordat-discussion-5.md` (the thread that started Weft) and
   `sources/aimode-2026-11-10-google.txt`.

## Open questions from review of weft PR #101 (E07 record, review by abu-aska, changes requested)
- perm.py shuffles single variants, but report section 5 says whole runs. Pick one and fix the text.
- colony.py splits count: fixed locally 2026-11-10 (counts `try`). Still to carry into the PR.

## How to run
- Python: `~/Work/exo-live/.venv/bin/python`. Do not poll jobs; wait for the job notice.
- Cheap paired run: `exp/run_cheap.sh OUTDIR MODEL [ARM]` (4 tasks, 16 calls, 8 steps,
  output cap 2000, effort low, 40k billed tokens per colony). Logs tokens and USD per cell.
- Full run template: `exp/run_e10.sh`. Pin model with `--model REF`; `routes` in summary.json shows who served.
- Knobs: CELL_ARM (ctrl, novar, safebold, ...), CELL_MODEL, CELL_MAX_OUT, CELL_EFFORT, CELL_TOKEN_BUDGET.

## Files
- `~/Work/razi-tools/cells/`: cell.py, colony.py (harness), e08.py, e08b.py, e10.py, e11.py, e12.py, e12b.py,
  mazecheck.py, e07art.py (analysis), embed.py, perm.py. Script outputs for E12 are in `exp/results/`.
  Old versions in `archive/`.
- `exp/`: TESTS.md (log + preregistrations), IDEAS.md (idea list), REPORT.html (report), needs*.json, run_*.sh.
- `~/Work/weft-repro/`: Paper 1 repro, E07 record, CPU vs MPS result.

## State on 2026-11-10, 02:30 CST (L1 judged)

- L1 is done and judged: 5 of 8 guesses held, the three that mattered missed. Result and diagnostics D1 to D8 are
  in TESTS.md ("L1 result", "L1 diagnostics"). Ideas L5 to L9 and next tests T-L2, T-L3 are in IDEAS.md section L.
- Short form: heredity saves (31% less energy, 7 deaths against 23) and does not search (reach level, 65 of 70
  heirs changed nothing). The gate took 3 of 4 real tries, so the block is the will to try, not the gate.
- Next: T-L2, division at birth (safe daughter keeps the body, bold daughter must change it or is born blank).
  Guesses before data. Baseline is arm h of L1. See `CONSULT-2026-11-10.md` (`~/Work/handoffs/weft-razi-cells-consult-20261110.md`) for the cross-project synthesis and ranked execution plan (`T-L2`, `metab.py` accounting fixes `L9`/`K18`, and `T-L3` deterministic work counters).
- Public: `Moissanite-Labs/weft` PRs #101 (E07 record), #107 (E11 to L1 record), and #110 (Siliconcordat Cut + Note 01) are merged on `main`.
- No job is running. Remove `~/Work/razi-cells/.bench.lock` before the next run if it is stale.
