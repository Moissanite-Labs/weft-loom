# razi-cells handoff at the session model switch (2026-11-09)

Written by the outgoing session model (anthropic:claude-opus-5-5, per exo_trace) for the incoming one (claude-fable-5-2).
Purpose: keep the experiment continuous, and make the change of analyst visible instead of silent.

## Rules that protect the data from the switch
1. Hypotheses in TESTS.md are judged as written. Do not reword a preregistration after data exists.
2. Numbers come from scripts (`~/Work/razi-tools/cells/e08.py`), not from reading logs by eye.
3. E10 was designed and preregistered before the switch. Analyse it with e08.py as is. If you want a
   different analysis, add it as a labelled second analysis, keep the first.
4. Python: `~/Work/exo-live/.venv/bin/python`. Do not poll jobs; wait for the job notice.
5. Never print or store keys. Cells have no network and no key.

## State
- E08 done: removing `variants` raised median final_gain from 4.2 (ctrl) to 11.5 (novar). Bold won 27 of 33.
- E09 partial (Argon hit its usage limit): nudging toward `try` did not change behaviour; cells kept
  calling `variants`. Current reading: tool affordance beats prompt instruction.
- E10 running (job j_8283a8): Fable 5.2 vs 5.1 x ctrl vs novar, 2 runs each. H8 to H11 in TESTS.md.
- Open PR: Moissanite-Labs/weft #101 (E07 record), needs one review.

## My beliefs, with confidence, so you can challenge them
| Belief | Confidence | Weakest point |
|---|---|---|
| `variants` is an attractor that blocks deep branches | medium | n is 1 to 3 runs per arm; Argon only |
| final_gain, not imp/100, is the right primary outcome | medium | heavy tails; one cell can be 2151x |
| Bold wins in cells but not in Weft because code edits are discrete, weight noise is smooth | low | untested story |
| Model matters less than tool design | low | E10 tests this directly |
| The 2 tampering cells in safebold do not change the E08 verdict | high | checked: verdict holds without them |

## What I would like a second perspective on
1. Is final_gain against the start assay biased toward arms that make many small adoptions, or against them?
2. Is there a better primary outcome than median final_gain (for example per-task rank across arms)?
3. Which report-3 variable should be tested next: apoptosis plus re-clone, elastic resistance near
   protected files, mutation rate tied to failing tests, or the fast reflex tier.

## Files
- `exp/TESTS.md` preregistrations and results. `exp/IDEAS.md` idea list. `exp/REPORT.html` report 1.
- `~/Work/razi-tools/cells/{cell.py,colony.py,e08.py}` harness and analysis. Arms via CELL_ARM.
- `exp/run_e0{8,9}.sh`, `exp/run_e10.sh` launchers.
