# Planned colony tests

Base for every run: needs8v3.json, --par 8 --calls 40 --steps 16 (same as g3/g4).
Score: kept wins per 100 calls, gain per win, wall time, done count, and cost when known.
Pin a model: `colony.py RUN needs.json --model REF` or a per-need `"model": REF` key.
A pinned cell has no hidden fallback. `routes` in summary.json shows who served every call.

Probed 2026-11-09: anthropic:claude-fable-5-1 ok (1.0s), openai:gpt-6-astra ok (1.9s).

## A. Baseline
- [x] g4: 1.57 wins/100 calls vs g3 3.12. Scale gate FAILS. No scaling.

## B. Homogeneous colonies (one model per colony)
- [ ] B1 opencode-go:deepseek-v4.1-flash (fast, cheap; = g4)
- [ ] B2 anthropic:claude-haiku-5-5 (fast)
- [ ] B3 anthropic:claude-sonnet-5-5 (mid)
- [ ] B4 anthropic:claude-opus-5-5 (deep)
- [~] B5 (running, pid 96800) anthropic:claude-fable-5-1 (high tier, requested)
- [~] B6 (running, pid 96801) openai:gpt-6-astra (high tier, requested, API key route)
- [ ] B7 off-frontier controls: nous:z-ai/glm-5.3-flash, nous:moonshotai/kimi-k3

## C. Fast vs powerful gradient
- [ ] C1 plot B1..B6 on calls, wall time, cost vs wins. Mark the Pareto frontier.
- [ ] C2 same caps by calls, then same caps by wall time (slow models lose on time, not calls).

## D. Mixed colonies (one colony, several models, shared LIBRARY)
- [ ] D1 4 fast + 4 high-tier cells on the same needs. Do fast cells reuse lessons from strong cells?
- [ ] D2 each need run twice in one colony: once fast, once strong. Head to head per task.

## E. Mixed roles inside one cell
- [ ] E1 strong model plans and picks variants, fast model writes code.
- [ ] E2 fast model by default, escalate to strong after 3 steps with no win.

## F. Repeatability
- [ ] F1 repeat the best 2 configs twice. Wins that do not repeat are noise.

## Watch for
- Which models use `variants` and the assay without being told.
- Library growth and whether lessons transfer across models.
- Bad replies or tool-call format faults per model.

## 2026-11-09 b7 (opencode-go:hy4) and b8 (opencode-go:gemini-4-argon), needs8v3, par 8, calls 40, steps 16
| Run | Done | Calls | Improvements | Per 100 calls | Wall s | Apoptosis |
|---|---|---|---|---|---|---|
| b7 hy4 | 7/8 | 123 | 0 | 0.00 | 3227 | 1 (csvsum) |
| b8 argon | 7/8 | 116 | 12 | 10.34 | 527 | 1 (csvsum) |
- hy4 never called variants/divide: 0 variants in all 8 cells. It optimized inside one shell script (compress: 12 encoders benchmarked in sh, picked ratio 14.29 by hand). Capability is there; it bypasses the selection machinery, so the metric reads 0. Slow too: ~200 s per call at the tail (lcs/maze/csvsum about 3000 s).
- Argon is close to Fable (12.82) and Astra (12.88) on per-100, with Fable-like wall time.
- csvsum died in both runs: check the need, not the model.
- Next for hy4: rerun with an explicit "use variants to compare options" nudge, to separate adherence from ability.

## Embedding A/B on b8 (first run with code captured, 33 variants)
E1 batch spread (nomic / 3-small / 3-large): maze n3 0.192/0.262/0.144 (ADOPTED, +10.5); sortints n6 0.108/0.249/0.254 (-0.0); fibmod n4 0.051/0.048/0.069 (+0.12); primes n4 0.035/0.021/0.038 (+0.41); maze n2 0.017/0.010/0.012 (+3.4).
- nomic and 3-small give the same rank order on all 5 batches. 3-large swaps the top two.
- The only adopted split was the widest batch under nomic and 3-small. n=5 batches, 1 adoption: no claim yet.
- Verdict for now: nomic (local, free) is enough for rank work. Keep 3-small as a check. More code-capturing runs needed before E1/E3 mean anything.
- b9: Fable rerun with code capture, for E5 cross-model fingerprints vs b8 (started 06:16)

## 2026-11-09 b9 Fable rerun (code captured)
- 8/8 done, 116 calls, 9 improvements, 7.76 per 100, 1069 s. b5 (same model, same needs) gave 12.82 in 360 s.
- Same model, two runs: 7.76 vs 12.82. Single-run gaps under ~5 per 100 are noise. Model rankings need 3+ reps per model.
- csvsum survived on Fable (2 improvements). So the csvsum deaths in b7/b8 are model-related, not a bad need. Correction to the b7/b8 note above.

## E5 fingerprints, b8 Argon vs b9 Fable (needs with 2+ variants in both runs: 6)
Rule: between-model centroid distance > larger within-run spread.
- nomic 5/6, 3-small 5/6, 3-large 5/6. The exception is sortints in all three (both models converge on similar code).
- maze and wordfreq show the widest gaps (0.22 to 0.43).
- Reading: models leave a detectable code fingerprint, except where the task has one obvious answer. All 3 embedders agree, so nomic stays the default.
- Caveat: crude test (centroid gap vs spread), n=6, one run per model. Next: a permutation test (shuffle model labels) once more code-capturing runs exist.
- b10 Argon rep, b11 Fable rep: variance + permutation test input (started 07:12)

## 2026-11-09 b10 (Argon rep) and b11 (Fable rep)
| Model | Runs | Per 100 calls | Mean |
|---|---|---|---|
| Fable | b5, b9, b11 | 12.82, 7.76, 11.02 | 10.53 |
| Argon | b8, b10 | 10.34, 12.50 | 11.42 |
- Fable and Argon cannot be told apart on improvement rate. Run-to-run spread (Fable 7.8 to 12.8) is larger than the gap between the models.

## E5 permutation test (cells/perm.py, 2000 shuffles, 3-small; 3-large agrees)
- Argon (b8+b10) vs Fable (b9+b11): 7/8 needs p<0.05. Looks like a fingerprint, but variants within a run share a lineage.
- Control, same model across runs: Argon b8 vs b10 1/5; Fable b9 vs b11 6/8.
- Cross-model single runs: b8 vs b9 4/6, b10 vs b11 4/7.
- Reading: Argon writes similar code run to run. Fable's runs differ from each other about as much as they differ from Argon. "Each model has a fingerprint" is NOT established. Better phrasing: models differ in run-to-run code diversity (Argon low, Fable high).
- Open question: does Fable's higher diversity buy anything? Its mean rate is not higher. Needs more reps.
- Ollama job j_7121a0 hit its 2h wall limit. Not needed: 3-small is the working embedder now.

## 2026-11-09 Report 1
- REPORT.html: full write-up of g1 to b11 (methods, results, validity threats, next experiments H1 to H8).
- New analysis in it: variants share vs improvements per 100 calls, r=0.991 over 8 runs (0.938 frontier only). Fable vs Argon Welch t=0.48.
- Report 1 v2: added method, variables, analysis plan, hypotheses H1 to H18 (registered before testing), roadmap. Found: only Astra (b6) ever used try (8 tries, 2 won).

## 2026-11-09 E08 preregistration: is `variants` the cause, and do bold proposals win?
Written before any E08 data. Model opencode-go:gemini-4-argon for every arm (fast, 10.34 and 12.50 per 100 in b8, b10).
Base: needs8v3.json, par 8, calls 40, steps 16. cell.py arm switch CELL_ARM (backup of the prior code: cell_v3e.py).
Arms: ctrl x1 (drift check against b8, b10), novar x3 (no variants tool, nudge points to try), safebold x3 (each
variant labelled safe or bold, half each). Waves of 4 then 3 colonies; the bench lock serialises timing.
Outcomes:
- O1 primary: final_gain per cell = final body median / assay baseline - 1, measured the same way in every arm.
  This counts hand edits too, so novar is not undercounted. Cells with no assay count as missing, not zero.
- O2: improvements per 100 calls (the old metric, comparable to b5..b11).
- O3 (safebold): share of adoptions whose winning version was labelled bold.
Hypotheses:
- H3: novar median final_gain is at most half of ctrl+safebold pooled. If not, variants was a marker, not the cause.
- H4: bold wins at least 25% of safebold adoptions (Weft beta won 0 of 120). If under 10%, cells agree with Weft.
- H5: safebold O2 is within 5 per 100 of ctrl (labels do not hurt the search).
Known limit: a cell can edit the files its assay reads. Check post hoc that winning diffs did not touch the assay script.

## 2026-11-09 E08 results (Argon, 7 colonies, 54 cells with an assay, 28 min)
| arm | runs | mean calls | imp/100 | median final_gain | cells |
|---|---|---|---|---|---|
| ctrl | 1 | 121 | 9.09 | 4.21 | 8 |
| novar | 3 | 188 | 5.98, 5.41, 6.15 | 11.50 | 22 |
| safebold | 3 | 113 | 9.65, 9.40, 10.09 | 1.09 | 24 |
- H3 REJECTED in the opposite direction. Without variants, median final gain is about 10x higher (11.50 vs 1.09 safebold),
  novar beats safebold on 7 of 8 tasks. Per call it is still about 6x. Permutation p for "novar worse" 0.998.
- The gains are scored, not hidden hand edits: novar median recorded gain 10.31 vs final 11.50. They come from `try` daughters.
- No novar cell edited its benchmark after registering it. 2 safebold cells did (e8s3 csvsum, sortints), so read those with care.
- Baselines are similar across arms per task, so a slow-baseline artefact does not explain it.
- Revision of report 1: imp/100 counts wins, not their size. variants gives frequent small wins, try gives rarer large ones.
  The old "variants is the channel" reading came from the metric, and the nudge pushed cells to variants.
- H4 SUPPORTED strongly: bold won 27 of 33 safebold adoptions (82%), offered 104 vs 104. Weft beta won 0 of 120.
- H5 SUPPORTED: safebold imp/100 9.40 to 10.09 vs ctrl 9.09. But its final gain is the lowest. Labels may push bold
  rewrites that win small steps but stop a cell from going deeper.
- Limits: ctrl is one run. One model. Gains are heavy-tailed (primes 2151x), so medians only.
- Open confound: novar changed both the tool set and the nudge. E09 separates them.

## 2026-11-09 E09 preregistration: tool or nudge?
Same base as E08. Arms: trynudge x3 (variants available, nudge says use try), free x3 (variants available, no
preference nudge), ctrl x2 (more control runs; E08 had one). Outcome O1 final_gain.
- H6: trynudge median final_gain is within 2x of novar (11.50). If so, the nudge was the cause, not the tool.
- H7: free cells choose try in at least 1 of 3 improvement calls on their own.

## 2026-11-09 E09 results (Argon, partial: 4 of 8 colonies; second batch died on HTTP 429 Go usage limit in 2 s)
Valid: e9t1, e9t2 (trynudge), e9f1 (free), e9c1 (ctrl). e9t3, e9f2, e9f3, e9c2: 0 calls, excluded.

| Arm | n cells | Median final_gain | imp/100 | variants calls | try calls |
|---|---|---|---|---|---|
| novar (E08) | 22 | 11.50 | 5.4 to 6.2 | 0 | many |
| trynudge | 16 | 4.06 | 9.92 / 7.63 | 13 / 11 | 1 / 1 |
| free | 8 | 5.66 | 10.32 | 16 | 0 |
| ctrl (E09) | 8 | 0.76 | 6.84 | 9 | 0 |

- H6 REJECTED: trynudge 4.06 is 2.8x below novar. Told to use try, cells used it once per colony and kept
  calling variants. The nudge does not move behaviour while the tool exists.
- H7 REJECTED: free cells called try 0 times.
- Reading: `variants` is an attractor. Its presence captures the cell's choices even against an explicit
  instruction. Removing it is what forces deep, single-hypothesis branches, and that is where the large gains
  come from. Tool affordance beats prompt instruction. Underpowered (n=1 or 2 runs per arm); replicate.

## 2026-11-09 E10 preregistration: Fable 5.2, and does the attractor effect hold across models?
2x2: model {anthropic:claude-fable-5-2, anthropic:claude-fable-5-1} x arm {ctrl, novar}, 2 runs per cell,
needs8v3, par 8, calls 40, steps 16. Batch 1: f52 ctrl, f52 novar, f51 ctrl, f51 novar. Batch 2: repeat.
Outcome O1 median final_gain per arm; O2 imp/100.
- H8: f52 ctrl median final_gain is at least 2x f51 ctrl (a weak test of "an order of magnitude better").
- H9: novar beats ctrl on median final_gain for both models (E08 attractor effect is not Argon specific).
- H10: f52 and f51 imp/100 within 5 of each other in the same arm (rate tracks tools, not model).
- H11: f52 uses fewer calls per improvement than f51 in novar (bigger model, fewer wasted steps).

### E10 results (analysed 2026-11-10, script `cells/e10.py`, analyst model changed to Fable 5.2 before analysis)
Routes check: every call in a/b runs was served by claude-fable-5-2, every call in c/d runs by claude-fable-5-1.
Preregistered analysis (E08 definitions, all cells):

| Arm | Runs | n cells | Median final_gain | imp/100 | Calls per imp |
|---|---|---|---|---|---|
| f52 ctrl | e10a1, e10a2 | 16 | 1.045 | 9.55 | 10.5 |
| f52 novar | e10b1, e10b2 | 16 | 2.387 | 0.88 | 113.5 |
| f51 ctrl | e10c1, e10c2 | 16 | 2.885 | 11.01 | 9.1 |
| f51 novar | e10d1, e10d2 | 15 | 0.024 | 0.78 | 128.0 |

- H8 rejected. f52 ctrl 1.045 vs f51 ctrl 2.885. The newer model did not gain more. Paired by task, f52 ctrl
  minus f51 ctrl has median -1.811, positive on 2 of 8 tasks.
- H9 rejected. novar beat ctrl on f52 (2.387 vs 1.045, 6 of 8 tasks) but lost on f51 (0.024 vs 2.885, 1 of 8).
  The E08 attractor effect did not replicate as a general rule. It is model dependent.
- H10 supported. ctrl 9.55 vs 11.01, novar 0.88 vs 0.78. In novar this is close to empty: each model had
  only 2 improvements, because without `variants` the only counted improvement is a `try` win.
- H11 nominally supported (113.5 vs 128.0) but it rests on 2 improvements per arm. Treat as no evidence.

Second analysis (not preregistered): scoring artifact found and removed.
- `measure` took the last number in stdout plus stderr. The library warning "OMP: Warning #179" on stderr
  was scored as 179.0. Affected E10 cells: e10a1/sortints, e10a2/csvsum (final 179.0, the 98.6 gain outlier),
  e10c2/maze, e10d1/sortints, e10d2/sortints. Same artifact appears in b5, e8c1, e8s3, g3, g4.
- With those cells dropped: f52 ctrl 1.045 (n 14), f52 novar 2.387 (n 16), f51 ctrl 2.183 (n 15),
  f51 novar 0.488 (n 13). H8 and H9 verdicts do not change. H11 flips (113.5 vs 112.5).
- Paired, artifact cells dropped: f52 novar minus f52 ctrl +1.461 (7 of 8 tasks). f51 novar minus f51 ctrl
  -0.142 (1 of 7). f52 novar minus f51 novar +1.732 (6 of 7).
- Fix applied 2026-11-10 in cell.py: score is the last number on stdout only, 0 on nonzero exit or timeout.
  Checked offline with three cases. colony.py now counts splits from `try` events (was "mitosis", never logged).

Reading, with limits:
- Model by tool interaction is the finding. Removing `variants` helped 5.2 and hurt 5.1. One reading: 5.2
  uses the freed calls for deep single-hypothesis work, 5.1 without the tool stalls. Not tested here.
- Limits: 2 runs per arm. Each cell writes its own bench, so final_gain is relative to a self-chosen baseline
  and is not comparable across cells in absolute terms. Earlier runs (E08, b5, g3, g4) carry the same artifact
  and need the same second analysis before the paper cites them.
- Cost: not logged (old code). Lesson recorded in the cheap protocol below.

### E08 and E09 second analysis (2026-11-10, script `cells/e08b.py`, not preregistered)
Question: do the E08 and E09 numbers survive removing cells touched by the stderr-179 scoring artifact?
Two exclusion levels. Strict: 179.0 is the cell's baseline, final, an assay run, or the adopted score.
Broad: the exact number 179.0 appears in any scoring event, including rejected variants. Matching is numeric.

| Arm | All cells n, median | Strict n, median | Broad n, median | Dropped (broad) |
|---|---|---|---|---|
| ctrl (e8c1) | 8, 4.206 | 7, 6.044 | 7, 6.044 | e8c1/sortints |
| novar | 22, 11.502 | 22, 11.502 | 22, 11.502 | none |
| safebold | 24, 1.085 | 22, 1.085 | 22, 1.085 | e8s3/primes, e8s3/sortints |
| trynudge | 16, 4.064 | 16, 4.064 | 16, 4.064 | none |
| free | 8, 5.661 | 8, 5.661 | 8, 5.661 | none |
| ctrl9 | 8, 0.758 | 8, 0.758 | 8, 0.758 | none |

- H3 stays rejected. Others minus novar: -9.948 with all cells (p 0.998), -9.768 with artifact cells
  dropped (p 0.997). Seeded permutation test, 5000 shuffles, seed 8.
- The headline "removing `variants` raised gain 4.2 to 11.5" becomes 6.0 to 11.5 against ctrl alone.
- Correction to how we have been stating it. novar against ctrl alone, two sided, is p 0.13 with all cells
  and p 0.20 with artifact cells dropped (n 22 vs 7). ctrl is one run. The gap is large but not established.
  The H3 rejection is solid mostly because safebold is low, not because ctrl is low.
- With E10 (helps Fable 5.2, hurts Fable 5.1) the honest statement is: removing `variants` raised gain
  on Argon in one comparison with a single control run, and the direction depends on the model.
- E10 broad level also drops e10c1/sortints, e10c2/primes, e10c2/sortints (179.0 only on rejected variants):
  f51 ctrl n 12, median 2.429. No verdict changes.
- Note on the artifact's direction. It can inflate (a slow or broken variant scores 179 and is adopted, as in
  e8c1/sortints, gain 72.9) or deflate (a good variant scores 179 below a true rate in the thousands and is
  rejected, as in e10c1/sortints). So it adds noise in both directions in ctrl arms, where `variants` runs.

## Cheap protocol (2026-11-10)
Reason: E10 ran about 1h12m per arm with no usage records. New default for all runs:
- needs4.json (compress, fibmod, csvsum, maze), 16 calls, 8 steps, par 4.
- CELL_MAX_OUT=2000, CELL_EFFORT=low, CELL_TOKEN_BUDGET=40000 per colony.
- Every step logs usage (inp, out, cr, cw, usd). colony.py summary reports tokens, usd, token_budget_hit.
- Paired design: the same 4 tasks for every arm. Compare per-task differences, medians only.
- Model choice (A, 2026-11-10): budget is unlimited and the project is top priority. The cost ladder (cheapest first: hy4, sonnet 5.5, gpt-6.1-sol (openai API), opus 5.5, astra, argon, fable) is for choosing without waste, not a rule to always use the cheapest.
  - Pick the model the question needs. Model comparisons, model mixes and frontier tests are valid science.
  - Waste = spend that buys no answer. Before any run: a preregistered question, usage logging on, a token budget set, the smallest design that can answer it.
  - Do a cheap pilot (smoke, 1 task) before a costly full run, so bugs are found on cheap calls.
- Smoke (sonnet 5.5, compress, 8 calls): 4 calls, 5932 billed tokens, $0.0255, 19s, rc 0.

## E11 preregistration (written 2026-11-10, before any E11 data)
Question: E08 had one ctrl run, so the `variants` effect is not established (two sided p 0.20). E10 showed the
direction depends on the model. Does removing `variants` help or hurt on a third model, with replication,
under the cheap protocol where steps are scarce?
- Model: anthropic:claude-sonnet-5-5. Reason: not yet tested, low on the cost ladder, native tools.
- Arms: ctrl, novar. 4 runs each, interleaved (c1, n1, c2, n2, ...), so time drift hits both arms equally.
- Protocol: cheap protocol as written below (needs4, 16 calls, 8 steps, par 4, max_out 2000, effort low,
  40k billed tokens per colony). Scoring is stdout only (fixed instrument).
- Pilot: one ctrl run (e11p). Purpose is feasibility only. Pilot data is excluded from the analysis.
  Stop rule: if fewer than 2 of 4 pilot cells reach an assay, the protocol is too short for this question;
  raise steps to 12 and calls to 24 for both arms, note it here, and rerun the pilot.
- Outcomes: O1 median final_gain per arm (cells with an assay). O2 improvements per 100 calls.
  O3 billed tokens per improvement. O4 share of cells that reach an assay.
- Analysis: per task, mean final_gain over the 4 runs in each arm, then novar minus ctrl. Report the median
  of the 4 task differences and the count of positive tasks. Also a seeded permutation test on cell medians
  (5000 shuffles, two sided). Limit known in advance: 4 tasks cannot reach p < 0.05 on a sign test, so the
  cell-level test carries the inference and treats cells as independent, which overstates n.
- H12: ctrl beats novar. Median of the task differences (novar minus ctrl) is below 0. Reason: with 8 steps
  one `variants` call buys several candidates, and novar must spend steps on write plus test.
- H13: at least 75% of cells reach an assay in both arms.
- H14: ctrl makes at least 5 improvements per 100 calls. novar makes fewer than ctrl.
- H15: novar spends more billed tokens per improvement than ctrl.
- If H12 fails with novar ahead, the E08 direction replicates on a third model. If it holds, the count
  stands at two models where `variants` helps (Fable 5.1, Sonnet 5.5) and two where it hurts (Argon, Fable 5.2).

### E11 pilot and run log (2026-11-10)
- Pilot e11p (ctrl, excluded from analysis): 4 of 4 cells reached an assay, so the stop rule did not fire and
  the protocol stands unchanged. 24 calls, 2 improvements, 42,991 billed tokens, $0.167, 75 s wall.
- Full run started right after as job j_8168a9 (`run_e11.sh full`), order c1, n1, c2, n2, c3, n3, c4, n4.
- Analysis script `cells/e11.py` was written while the run was in progress and before any arm data was read.
  It was checked only on the pilot folder (`e11.py selftest`, both arms pointed at e11p).
  One reading had to be fixed in advance because the preregistration is loose: "permutation test on cell
  medians" is taken as median(novar cells) minus median(ctrl cells) on final_gain, cell labels shuffled,
  5000 shuffles, seed 0, two sided.
- No instrument file (`cell.py`, `colony.py`) is edited while the run is in progress.
