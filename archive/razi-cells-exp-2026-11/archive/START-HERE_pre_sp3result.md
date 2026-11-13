# razi-cells: start here (2026-11-10)

Read this, then TESTS.md. Older handoff and report v1 are in `exp/archive/`.
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

## Next
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
