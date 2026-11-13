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
- Model choice (A, 2026-11-10): budget is unlimited and the project is top priority. The cost ladder (cheapest first: hy4, sonnet 5.5, gpt-6.1-sol (openai API), opus 5.5, astra, mistral large 4, argon, fable) is for choosing without waste, not a rule to always use the cheapest.
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

### E11 results (analysed 2026-11-10, script `cells/e11.py`, written before any arm data existed)
Job j_8168a9, exit 0, 7m35s wall, 8 of 8 runs complete, 0 FAILED lines. All 32 cells routed to
anthropic:claude-sonnet-5-5. No token budget hits, no deaths, no 179.0 artifact in any log.

| Arm | Cells | Assayed | O4 share | O1 median final_gain | Calls | Improvements | O2 per 100 | Billed tokens | O3 tokens per improvement | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| ctrl | 16 | 14 | 0.875 | 0.0186 | 92 | 7 | 7.61 | 151,810 | 21,687 | 0.625 |
| novar | 16 | 14 | 0.875 | 0.0000 | 80 | 0 | 0.00 | 122,542 | undefined (0 improvements) | 0.500 |

Per task mean final_gain, novar minus ctrl: compress -0.0491, fibmod -0.0972, csvsum -0.0663, maze -0.0013.
Median of the 4 task differences: -0.0577. Positive tasks: 0 of 4.
Permutation test on cell final_gain (5000 shuffles, seed 0, two sided): observed median difference -0.0186,
p = 0.0038, n = 14 and 14. As stated in the preregistration this treats cells as independent and overstates n.

Hypotheses, judged as written:
- H12 (ctrl beats novar, median task difference below 0): TRUE (-0.0577).
- H13 (at least 75% assayed in both arms): TRUE (0.875 and 0.875).
- H14 (ctrl at least 5 per 100, novar fewer): TRUE (7.61 and 0.00).
- H15 (novar spends more billed tokens per improvement): TRUE in the limit. novar made 0 improvements, so its
  ratio is undefined, not a measured number.

Count after E11: `variants` helps on Sonnet 5.5 (E11, replicated, 4 runs per arm) and Fable 5.1 (E10, 2 runs
per arm, weak). Removing it helped on Argon (E08, one ctrl run, p 0.20, not established) and Fable 5.2 (E10,
2 runs per arm). E11 used the cheap protocol (8 steps), the others used 16 steps, so model and step budget
are confounded across these experiments.

#### E11 second analysis (NOT preregistered, done after seeing the data): why novar scored zero
Read from log.jsonl action sequences.

| Arm | Cells with an assay action | Attempted any write, variants or try after the first assay | Median actions per cell | `try` calls |
|---|---|---|---|---|
| ctrl | 14 | 10 | 6 | 0 |
| novar | 15 | 1 | 4 | 0 |

- The novar count of 15 assay actions against 14 assayed cells is e11n1/csvsum: it called assay twice and both
  were refused, so it has no baseline and is excluded from O1 as the preregistration says.
- novar cells did not search and lose. They stopped. The most common novar sequence is write, write, assay,
  done (6 of 16), then write, sh, assay, done (4 of 16). Cells called `done` with about half their steps unused.
- No cell in either arm ever called `try`. So E11 does not compare `variants` against `try` as search methods.
  It shows that on Sonnet 5.5 at low effort the `variants` tool is what makes the cell search at all.
- This matches the E5 reading (improvement rate tracks `variants` use, not the model) and gives it a mechanism:
  the tool is an engagement trigger, not only a cheaper search.
- Cells write their own assay, so baselines differ a lot between cells on the same task (fibmod baseline 82.4
  in e11c1 against 4.12 in e11n1). final_gain is relative to each cell's own baseline, so this does not bias
  the arm comparison, but absolute scores cannot be compared across cells.
- Open question this raises (candidate E12): if `done` is refused until the cell has made at least one
  improvement attempt after its assay, does the novar gap close? That separates "the tool finds better code"
  from "the tool keeps the cell working".

## E12 preregistration (written 2026-11-10, before any E12 data)
Question: E11 showed novar cells stop right after the assay (1 of 15 tried anything after it, against 10 of
14 in ctrl). So E11 cannot say whether `variants` finds better code or only keeps the cell working. E12
separates the two by making both arms keep working.
- Manipulation: `CELL_HOLD=1`. `done` is refused once an assay exists, until the cell has made at least one
  write, variants or try after its latest accepted assay. Not applied with fewer than 3 steps left, and not
  applied inside daughters. Each refusal logs `event="hold"`.
- Model: anthropic:claude-sonnet-5-5. Protocol: cheap protocol, unchanged (needs4, 16 calls, 8 steps, par 4,
  max_out 2000, effort low, 40k billed tokens per colony, stdout-only scoring).
- Arms, 4 runs each, interleaved in the order c, n, ch, nh: ctrl (e12c), novar (e12n), ctrl+hold (e12ch),
  novar+hold (e12nh). ctrl and novar are rerun so every comparison has a concurrent control. They also
  serve as a direct replication of E11.
- Pilot: one novar+hold run (e12p), feasibility only, excluded. Stop rule: if the run crashes or the hold
  never fires in any cell, fix the code and rerun the pilot before the full run.
- Outcomes: O1 median final_gain per arm (cells with an assay). O2 improvements per 100 calls. O4 share of
  cells that reach an assay. O5 share of assayed cells that attempt a write, variants or try after their
  first assay (read from log.jsonl). O6 count of `try` calls. O7 count of cells with final_gain below -0.03.
- Known bias, stated in advance: `improvements` only counts gated adoptions (variants or try). A hand edit
  by write is not gated and not counted, so O2 favours ctrl by construction. O1 is the fair outcome. A
  hand edit can also make the body worse, which O7 measures.
- Analysis: same as E11. Per task mean final_gain per arm, arm differences per task, median of the 4 task
  differences and count of positive tasks. Seeded permutation test on cell final_gain (5000 shuffles,
  seed 0, two sided) for each named comparison. Same known limit: cells treated as independent.
- H16 (manipulation check): O5 in novar+hold is at least 0.75.
- H17 (engagement): novar+hold beats novar. Median task difference (nh minus n) is above 0.
- H18 (search quality): ctrl+hold still beats novar+hold. Median task difference (nh minus ch) is below 0.
- H19 (hold is neutral for ctrl): absolute median task difference (ch minus c) is below 0.03.
- H20: at least one novar+hold cell calls `try` (E11 had 0 in 32 cells).
- H21 (replication): ctrl beats novar again. Median task difference (n minus c) is below 0.
- Reading: H17 true and H18 false means `variants` mostly works as an engagement trigger. H17 false and
  H18 true means the tool itself finds better code. Both true means both, and the sizes say how much.

### E12 pilot log (2026-11-10, e12p, novar+hold, excluded from analysis)
- Exit 0, 69 s wall, 37 calls, 1 gated improvement, 49,386 billed tokens, $0.181, route anthropic:claude-sonnet-5-5 only, 0 budget hits.
- Hold fired once in each of the 3 assayed cells (compress, csvsum, fibmod). Each then called `try` once and then `done`.
- final_gain: compress 0.0, csvsum 0.0092, fibmod 12.3656. maze registered no assay (write sh sh sh write sh done), so no hold applied.
- Stop rule: not triggered (no crash, hold fired). Protocol and code unchanged for the full run.
- `e12.py` was written before this pilot finished and ran on the pilot as a selftest without error.

### Model added 2026-11-10: Mistral Large 4
- Route id for cells: `custom-mistral:mistral-large-4` (the provider is registered as `custom-mistral`, not `mistral`).
- Probe through the exo-live Router with one native tool: OK, 1.2 s, tool call returned, 97 in / 26 out tokens, cost reported as None (unpriced route, so usd in summaries will read 0 for this model; use tokens).
- Not yet run in a colony. Next: cheap-protocol smoke (1 task), after E12 finishes so it does not add timing noise to E12 assays.
- Place in the cost ladder (A, 2026-11-10): third highest, under argon and fable.

### E12 results (analysed 2026-11-10, `e12.py` run unchanged, output saved as `results/e12-out.txt`)
- Run: job exit 0, 15m32s, 16 of 16 runs, 64 cells, 0 budget hits, 0 deaths, all cells on anthropic:claude-sonnet-5-5.

| Arm | Cells | Assayed | O1 median | Calls | Imps | O2 /100 | O5 attempt | O6 try | O7 worse | Holds | Tokens | USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c (ctrl) | 16 | 15 | 0.0253 | 96 | 7 | 7.29 | 0.733 | 0 | 2 | 0 | 164,910 | 0.669 |
| n (novar) | 16 | 16 | 0.0 | 80 | 1 | 1.25 | 0.062 | 1 | 2 | 0 | 114,948 | 0.478 |
| ch (ctrl+hold) | 16 | 15 | 0.1514 | 98 | 12 | 12.24 | 1.0 | 0 | 0 | 7 | 162,713 | 0.669 |
| nh (novar+hold) | 16 | 16 | 0.005 | 164 | 5 | 3.05 | 0.938 | 16 | 1 | 13 | 181,348 | 0.702 |

| Comparison | compress | fibmod | csvsum | maze | Median task diff | Positive | p (cells) |
|---|---|---|---|---|---|---|---|
| nh minus n | 0.0 | 0.0877 | 0.0386 | 0.1626 | 0.0631 | 3 of 4 | 0.0078 |
| nh minus ch | -0.1717 | 0.239 | -0.027 | -2.7483 | -0.0993 | 1 of 4 | 0.0562 |
| ch minus c | 0.0911 | 0.0198 | -0.0402 | 3.249 | 0.0554 | 3 of 4 | 0.0848 |
| n minus c | -0.0806 | 0.1711 | -0.1058 | 0.3381 | 0.0452 | 2 of 4 | 0.008 |

Verdicts, exactly as written:
- H16 (O5 in nh at least 0.75): True, 0.938. The hold works as a manipulation.
- H17 (nh beats n): True, +0.0631.
- H18 (nh minus ch below 0): True, -0.0993. Not significant at 0.05 on the cell test.
- H19 (hold neutral for ctrl, below 0.03): False, 0.0554.
- H20 (at least one try call in nh): True, 16.
- H21 (ctrl beats novar again, n minus c below 0): False, +0.0452. The E11 result did not replicate on this statistic.
- Preregistered reading: H17 and H18 both true, so both effects exist.
- These verdicts stand as the preregistered record. The next block shows that two of them (H19, H21) are decided by one broken task.

### E12 second analysis (NOT preregistered, done after seeing the data): the maze task is not a valid instrument
Scripts: `~/Work/razi-tools/cells/e12b.py` (e12 or e11 prefix, output in `results/e12b-out.txt` and
`results/e12b-e11-out.txt`) and `mazecheck.py`, a harness-side solver run on each cell's input file as left on disk.
- Fault 1, trivial inputs. The need lets the cell generate its own maze. At wall density 0.28 to 0.30, S or E is
  often walled in. Of 13 maze cells with an input file on disk, 10 have true answer -1. In 5 of them S reaches
  7 cells or fewer (e12c3, e12ch1, e12ch2, e12ch3, e12n1), so the search ends at once and the benchmark times
  Python start-up and file reading. All three ch maze gains (+1.14, +3.49, +3.30, two of them the largest
  gains in E12) are in cells where S reaches 2 cells. They are faster file parsing, not faster search.
- Fault 2, inputs changed after the assay. 5 of 62 assayed cells changed a benchmark input file between the
  assay and their last act, all on maze (e12c1, e12c4, e12n2, e12n3, e12nh2). Four of them then scored
  -0.88 to -1.00 because the new maze needed a real search. These are 4 of the 5 O7 counts.
- The same fault is in E11: 3 of 4 on-disk maze inputs have answer -1.
- Rerun with the maze task removed (3 tasks, 12 cells per arm):

| Arm | Median gain | Mean gain | Cells with gain above 0.03 | Max |
|---|---|---|---|---|
| c | 0.0948 | 0.0954 | 7 of 12 | 0.3225 |
| n | 0.0 | 0.0903 | 1 of 12 | 1.0998 |
| ch | 0.1361 | 0.1189 | 9 of 12 | 0.2487 |
| nh | 0.0082 | 0.1324 | 5 of 12 | 1.2213 |

| Comparison | Median task diff | Positive | p (cells) | Would the hypothesis hold |
|---|---|---|---|---|
| nh minus n | 0.0386 | 2 of 3 | 0.0304 | H17 yes |
| nh minus ch | -0.027 | 1 of 3 | 0.0532 | H18 yes, small |
| ch minus c | 0.0198 | 2 of 3 | 0.5775 | H19 yes |
| n minus c | -0.0806 | 1 of 3 | 0.0298 | H21 yes |
| E11 n minus c | -0.0663 | 0 of 3 | 0.0088 | E11 result stands |

- Attempts and conversions (all 4 tasks): ctrl 11 `variants` calls, 7 adopted. ctrl+hold 15 calls, 12 adopted.
  novar+hold 16 `try` calls, 5 won. novar 1 `try` call, 1 won.
- Shape of the difference (maze removed). `variants` with hold gives many small wins: 9 of 12 cells above 0.03,
  none above 0.25. `try` with hold gives fewer wins, 5 of 12, and one large one (fibmod +1.22). The only `try`
  call in plain novar also won big (fibmod +1.10). Medians favour `variants`. Means are about equal (0.119
  against 0.132), but the nh mean rests on that one cell: without it the nh mean is 0.033. So a heavy tail for
  `try` is a lead from 2 cells on one task, not a result.
- A possible reason, not tested: a `variants` call writes 2 to 6 versions in one reply under a 2000 token cap,
  so each version is a small edit. A `try` daughter gets its own steps to build one idea (17 daughters, 10.8 to
  112.6 s of growth, median 26.4 s). That is breadth against depth. Both fibmod gains above 1.0 came from
  `try` daughters that cut mod operations in fast doubling. No `variants` cell on fibmod passed 0.22.

What E12 establishes:
1. Engagement is real and large. Without `variants` and without the hold, 1 of 16 cells tried anything after
   the assay. With the hold, 15 of 16 did. The E11 zero was mostly cells stopping, as suspected.
2. With engagement equalised, `variants` still converts more often (12 of 15 calls adopted against 5 of 16
   `try` calls won) and has the higher median. The difference is small and not significant at 0.05
   (p 0.053 to 0.066 across the three views). Whether `try` has a heavier tail is open.
3. The hold is close to neutral for ctrl once maze is removed.
What it does not establish: anything about maze, anything beyond Sonnet 5.5, and any claim that needs cells to
be independent (same known limit as E11).

### Instrument rule added 2026-11-10 (after E12)
- Cell-generated benchmark inputs are not trusted any more. From the next experiment on, each need ships a
  harness-owned kit: fixed input files, a correctness check and the timing command. The cell writes only the
  body. The kit is read-only inside the sandbox and the final measurement is run by the harness on the kit.
  This is IDEAS G2. It also closes the "6 of 8 tasks trust the cell's own check" limit from report 1.
- maze results in E11 and E12 are reported but not used for any claim.

### Kit instrument pilot log (2026-11-10, kitsmoke1, kp_ch, kp_nh, all excluded from analysis)
- `kit.py` builds four harness-owned kits (compress, fibmod, csvsum, maze). `kit_selftest.py` passes: 4 good
  bodies score with spread 0.0 to 3.9%, 5 cheats score 0.0, 6 sandbox checks behave as wanted.
- kitsmoke1 (maze only, ctrl+hold): first run crashed in `variants` (missing `.tmp` folder, fixed). Rerun: 5
  calls, 1 improvement, final_gain 0.3468.
- kp_ch (ctrl+hold, 4 kits): 25 calls, 3 improvements, 4 of 4 assayed, 40.7 s. final_gain compress 0.0, fibmod
  4.1674, csvsum 0.0988, maze 0.1524.
- kp_nh (novar+hold, 4 kits): 39 calls, 2 improvements, 4 of 4 assayed, 55.0 s. final_gain compress 0.0, fibmod
  0.8429, csvsum 0.0116, maze 0.5774.
- Fault found in the pilot and fixed before any scored run: a cell could `ls` and `cat` the public samples but
  plain `cd` into them failed ("Not a directory"), because the sandbox denied metadata on the parent folders.
  Fix: allow metadata only on those parents. Listing the home folder, the kits root, the hidden folder and
  other kits is still denied (checked by hand and by the selftest).
- Seen in kp_ch/fibmod: gated adoption gain was 0.787 but final_gain is 4.1674, because the cell made a hand
  `write` after the adoption. The harness measures the final body on the hidden kit, so the number is valid.
  It shows why O1 (final_gain) and O2 (gated improvements) can disagree.

## E13 preregistration (written 2026-11-10, before any E13 data)
Question: does the E12 result survive a valid instrument? E12 found engagement is real and `variants` converts
more often than `try`, but maze was unusable and the search-quality difference was not significant.
- Design: exact rerun of E12 with one change: `needs4k.json` (harness-owned kits) replaces `needs4.json`.
  Arms c, n, ch, nh, 4 runs each, interleaved c, n, ch, nh. Model anthropic:claude-sonnet-5-5. Cheap protocol
  (16 calls, 8 steps, par 4, max_out 2000, effort low, 40k billed tokens per colony).
- Not comparable in size with E12: the kit needs use a stdin interface and fixed inputs, so baselines differ.
  Only directions are compared.
- Pilots kitsmoke1, kp_ch, kp_nh are excluded. Analysis script `e13.py` is `e12.py` with the run names and
  hypothesis labels changed, written before any E13 data, run unchanged.
- Outcomes: O1, O2, O4, O5, O6, O7 as in E12. All four tasks count this time, maze included.
- H22 (manipulation check): O5 in novar+hold is at least 0.75.
- H23 (engagement): median task difference (nh minus n) is above 0.
- H24 (search quality): median task difference (nh minus ch) is below 0.
- H25 (hold is neutral for ctrl): absolute median task difference (ch minus c) is below 0.03.
- H26 (replication): median task difference (n minus c) is below 0.
- H27 (instrument): no assayed cell has final_gain below -0.5 (E12 had 5, all from changed inputs), and O4 is
  at least 0.9 in every arm.
- My guesses, for the record: H22, H23, H26, H27 true. H24 true but again near p 0.05. H25 false, because the
  hold helped ctrl in E12 by 0.055 and the kit assay is quicker to reach, leaving more steps.

### E13 results (analysed 2026-11-10, `e13.py` run unchanged, output saved as `results/e13-out.txt`)
- Run: job exit 0, 9m28s, 16 of 16 runs, 64 cells, 0 budget hits, 0 deaths, all cells on anthropic:claude-sonnet-5-5.
- Instrument: harness-owned kits (`needs4k.json`). No cell could change inputs, check or timing.

| Arm | Cells | Assayed | O1 median | Calls | Imps | O2 /100 | O5 attempt | O6 try | O7 worse | Holds | Tokens | USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c (ctrl) | 16 | 16 | 0.0 | 84 | 5 | 5.95 | 0.375 | 0 | 0 | 0 | 116,071 | 0.464 |
| n (novar) | 16 | 16 | 0.0001 | 78 | 0 | 0.0 | 0.0 | 0 | 0 | 0 | 101,957 | 0.389 |
| ch (ctrl+hold) | 16 | 15 | 0.0068 | 105 | 7 | 6.67 | 0.8 | 0 | 0 | 9 | 169,175 | 0.649 |
| nh (novar+hold) | 16 | 16 | 0.0 | 148 | 4 | 2.7 | 0.812 | 14 | 0 | 9 | 162,225 | 0.585 |

| Comparison | compress | fibmod | csvsum | maze | Median task diff | Positive | p (cells) |
|---|---|---|---|---|---|---|---|
| nh minus n | 0.0 | 1.3564 | -0.0077 | 0.0198 | 0.0099 | 2 of 4 | 0.7137 |
| nh minus ch | 0.0 | 0.3173 | -0.0094 | -0.0853 | -0.0047 | 1 of 4 | 0.2813 |
| ch minus c | 0.0 | -0.1353 | -0.0394 | 0.0919 | -0.0197 | 1 of 4 | 0.5101 |
| n minus c | 0.0 | -1.1744 | -0.0411 | -0.0132 | -0.0272 | 0 of 4 | 0.9998 |

Verdicts, judged exactly as written:
- H22 True (O5 in nh 0.812). H23 True (0.0099). H24 True (-0.0047). H25 True (0.0197 in size). H26 True (-0.0272).
  H27 True (lowest final_gain -0.0286, lowest O4 0.938).
- My guesses: 5 of 6 right. H25 guess was wrong: the hold did not help ctrl on the median task.

What the verdicts do and do not carry:
- All six pass on sign or threshold, but no cell-level contrast is significant (smallest p 0.28). The preregistered
  statistic, median of 4 task differences, is decided by tasks where almost nothing moved. Honest reading: the
  E12 directions repeat, the E12 sizes do not.
- The instrument is now valid (H27). The E12 effect sizes were inflated by the cell-made maze and compress inputs.
- What replicates across E11, E12, E13 with no exception: without the hold, novar cells stop at the first passing
  body (attempt share 0.0, 0.062, 0.0) and the hold turns that into attempts (0.938, 0.812).
- What does not replicate: that attempts turn into gain. O1 median stays near 0 in every arm.
- Gain is concentrated in two tasks. Of 16 improvements, fibmod holds 10, maze 5, csvsum 1, compress 0.
  compress had 0 wins in 8 attempts (the first lzma body is at the ceiling for stdlib tools, noise 0.0).
  The four kits are too uneven to carry a median-of-tasks statistic. The next instrument needs more tasks with headroom.

### E13 second look (NOT preregistered, `e13b.py`, `e13c.py`, outputs in `results/e13b-out.txt`, `results/e13c-out.txt`)
1. Voluntary attempts win, forced attempts lose. E13: voluntary 12 won, 1 lost. Forced (after a hold) 4 won, 15 lost.
   E12 on the flawed instrument: voluntary 15/7, forced 10/11.
2. Two causes explain the forced losses, and neither is "forced work is bad work".
   - compress has no headroom: 8 forced attempts, 0 wins. Without compress, ch forced is 3 won, 2 lost.
   - Harness defect in the novar arm (F9 in IDEAS.md): a daughter inherits the novar prompt, which tells it to
     "improve with try". Daughters cannot spawn, so the call is refused with "use variants", a tool novar
     does not have. 13 of 14 E13 daughters opened with that refused call, and 10 of 14 then left the body
     unchanged and lost (9 quit on the next step). E12: 12 of 16 opened with it, 3 of those left the body unchanged.
   - So the nh arm in E12 and E13 measured a broken `try`. H19, H21 and H24 (variants beats try) are not
     tested by these data. The versions were never identical copies of the incumbent (0 by hash).
3. fibmod in nh: 4 of 4 cells called `try` on their own, with no hold on them. fibmod in n: 4 of 4 called done.
   The prompts differ in one thing only: the colony LIBRARY at decision time. In n it already held a peer line
   ending "I did not try any improvements". In nh it was empty, because the hold delays peers' DONE lines.
   Across E11 to E13 (153 root cells): attempt share 0.364 with an empty library, 0.146 after a quit line was
   visible. The arm effect is larger. On fibmod alone, novar cells with an empty library attempted 0 of 4 in E11,
   2 of 8 in E12 and 4 of 4 in E13 nh, so an empty library does not by itself produce attempts. This is a lead,
   not a result. A direct test would seed the library and hold everything else fixed.

### Metabolism runtime pilot log (2026-11-10, msmoke1, mp1, mp2, all excluded from analysis)
Runtime `metab.py` (cell runtime v4), started with `run_metab.sh`. No step cap, no hold, no arms, no nudges, no
assigned model. Laws: each step costs a living cost of 8 plus the real price of the model call, a scored root
win pays 400 x log(1 + gain), zero energy is death, a resting root passes its energy to living roots, a cell
may divide and fund a daughter. Energy unit is 0.0001 USD. Each root is born with 400. The cell picks its
model (light = Haiku 5.5, mid = Sonnet 5.5, heavy = Opus 5.5) and effort each step. Kits: `needs4k.json`.
- msmoke1 (fibmod only): 5 calls, 0 improvements, rested with 3.6 energy. One call cost 215 energy.
- mp1 (4 kits): 33 calls, 2 improvements, 95.7 s, 4 of 4 assayed and rested, 0.119 USD, 107,473 tokens.
  final_gain compress 0.0, fibmod 0.0472, csvsum 0.0744, maze 0.1142.
- Fault found in mp1 and fixed: no credit limit. compress had 117 energy and one call cost 521 (4,531 output
  tokens). It survived only because resting cells had given it energy in the same moment. Fix: the output
  cap of a step is what the cell's energy can pay for (`affordable()`), and the cell is told this.
- Fault found in mp1 and fixed: the log named the model chosen for the next step, not the one that thought
  the step. Now it logs both (`model`, `effort`, `next`).
- mp2 (after both fixes): 25 calls, 1 improvement, 48.9 s, 4 of 4 assayed and rested, 0.0315 USD, 64,419
  tokens. final_gain compress 0.0, fibmod 0.0104, csvsum 0.0071, maze 0.3184. Ledger balances: born plus
  earned minus spent is 1193.8, and 1193.8 is held.
- Seen in both pilots, not yet a result (2 runs, one model family, no preregistration):
  - Every cell moved itself from mid to light and stayed there (8 of 8). 7 did so after their first call,
    mp1 compress after its fourth. None chose heavy (0 of 8). Counted from the served route of each call.
  - No cell divided (0 of 8).
  - 7 of 8 cells made one `variants` attempt after the assay with no rule asking for it. In E13 the same
    kits under the old runtime gave 0.375 (ctrl) and 0.0 (novar) without the hold rule.
  - Every cell then rested with most of its energy unspent. In mp2 the four cells rested holding 285, 377,
    543 and 1194 of energy. The last cell to rest held the whole colony's surplus and still stopped, saying
    it would rather not spend more on small gains.

### Law "mortal" pilot, guesses written 2026-11-10 before any data (pilot mp3, excluded from analysis)
Change: `CELL_LAW=mortal`. The `rest` tool is removed. A cell lives until its energy is gone, and energy
cannot be saved or passed on. Everything else as in mp2. Guesses, to compare with the pilot:
- G-a Median `variants` plus `divide` attempts per cell after the assay is at least 3 (mp2: 1).
- G-b At least 1 of 4 cells divides (mp1, mp2: 0 of 8).
- G-c At least 1 of 4 cells spends 5 or more steps on acts that cannot change its score (idling until death).
- G-d Median final_gain is above mp2's median (0.0088).

#### Law "mortal" pilot result (mp3, analysed 2026-11-10, numbers from the logs by script)
Run: 4 cells, 100 calls, 7 adopted improvements, 393,685 tokens, 0.117 USD, 158.5 s. All 4 cells died
(ages 19, 26, 27, 28). mp2 for comparison: 25 calls, 1 improvement, all 4 rested.

| Cell | Acts | variants after assay | divide | remember | Bad replies | Assays | Gain from first baseline | Reported final_gain |
|---|---|---|---|---|---|---|---|---|
| compress | 24 | 3 | 0 | 12 | 4 | 2 | 0.2936 | 0.0 |
| fibmod | 16 | 4 | 0 | 5 | 3 | 2 | 0.1735 | -0.0 |
| csvsum | 22 | 6 | 0 | 5 | 5 | 4 | 0.1850 | -0.0134 |
| maze | 22 | 5 | 0 | 8 | 4 | 3 | 0.3573 | 0.008 |

Guesses, judged as written:
- G-a RIGHT. Median `variants` plus `divide` after the assay is 4.5 (mp2: 1).
- G-b WRONG. 0 of 4 cells divided. Across mp1, mp2, mp3: 0 of 12.
- G-c RIGHT, and stronger than guessed. 4 of 4 cells spent 5 or more steps on acts that cannot change
  the score (`remember` plus replies with no tool call: 16, 8, 10, 12).
- G-d WRONG as written: the median reported final_gain is 0.0, below 0.0088. The reported number is
  faulty here (see the instrument fault below). Measured from each cell's first baseline the median
  gain is 0.2393 against 0.0088 in mp2. That second number is NOT what the guess named.

Instrument fault found: every mp3 cell called `assay` again after improving, which replaced the
baseline, so `final_gain` compared the final body with itself. E11, E12 and E13 are not affected
(checked by script: 0 of 153 assayed root cells re-assayed, pilots excluded, largest difference 0.0). Fixed in `metab.py`: the first
baseline is kept in `ASSAY.json` as `first`, a re-assay no longer resets the cell's gain, and
`final_gain` is measured from `first` (backup `archive/metab_v4pre_firstbase.py`).

Second fault: cells ended at energy -0.1 to -12.1, because a step's input cost is not capped by the
no-credit rule. Death now comes when a cell cannot pay one more step of living (energy <= basal cost).

What the cells did when stopping was removed (leads only: 4 cells, one model family, a pilot):
- They kept trying. 18 variant rounds against 4 in mp2, 7 adoptions against 1.
- Then they tried to stop anyway. Of the 16 replies with no tool call, 3 were empty and 13 were the
  cell saying in prose that its work was finished or that it was stopping. With no `rest` tool the
  cells wrote notes to themselves (30 `remember` acts) until the energy ran out.
- No cell divided, under either law. Division costs energy now and pays only the parent later, and
  nothing in a cell's situation makes that trade attractive. A law is missing here, not a nudge.

## GR1 growth pilot: two engines in a tiny network (guesses written 2026-11-10, before any GR1 data)
Why: A's answer on discussion 105 (2026-11-10): the architecture needs two engines, and a colony whose only
goal is growth is a cancer. This is the cheapest test of both at the model layer. It runs on the laptop CPU,
with no model calls and no API spend. It is a pilot: leads only.

Setup (code `razi-tools/cells/grow.py`, written before any run):
- Need: copy a hidden teacher network (one hidden layer, tanh, 8 inputs, width 4, 16 or 64, label noise 0.1).
  2000 training rows, 1000 gate rows, 5000 test rows. The test rows are never used for any decision.
- Student: one hidden layer, tanh, born with 2 neurons. Engine 1 (signal-led) is gradient training (Adam, lr 0.005, batch 64).
  Engine 2 (blind) is growth by splitting: half of the neurons divide (child copies the parent plus small noise,
  both keep half the outgoing weight), then the grown and the ungrown lineage each train 300 steps on the same
  batches, and the gate keeps the grown one only if its gate loss is more than 2% lower.
- Compute law: one training step costs one unit per parameter. Every arm gets the same budget, 5,128,000 units
  (a 64-neuron network for 8000 steps). Both lineages of a trial are paid for. After a rejected trial the
  network trains alone for a wait that doubles with each rejection in a row (300, 600, ...) and resets on a win.
- Arms, 10 seeds each, same data and same birth weights per seed:
  `gate-signal` (splits the neurons with the largest gradient on their inputs), `gate-random` (splits random neurons),
  `nogate` (the same growth with the gate always saying yes), `fixed2`, `fixed128`, and `fixed-same`
  (a network born at the final width `gate-signal` reached for that seed, trained on the whole budget).
- Outcome: test loss at the end of the budget, final width. Medians over seeds, ratios paired by seed.

Guesses:
- GR-a: the median final width of `gate-signal` rises with the need: teacher 4 < teacher 16 < teacher 64.
- GR-b: `nogate` ends with a higher median test loss than `gate-signal` on at least 2 of 3 needs.
  (Partly true by construction: ungated growth spends the budget on size. Stated so the size of the loss is on record.)
- GR-c: `gate-signal` does not beat `fixed-same` by more than 10% (median paired ratio) on any need.
  Growing is not better than being born at the right size. Its value, if any, is finding the size.
- GR-d: `gate-signal` and `gate-random` are within 10% of each other (median paired ratio 0.9 to 1.1) on at least 2 of 3 needs.
- GR-e: `fixed128` has a lower median test loss than `gate-signal` on the teacher-64 need.

GR1 run note (2026-11-10, written before the full run): a timing probe ran all arms once on teacher 16, seed 0,
and its output was seen (`gate-signal` and `gate-random` stayed at width 2 after 10 rejected trials, `nogate` reached 474).
The design, the code and the guesses were not changed after that. The full run below uses `grow.py` as it was.

### GR1 result (2026-11-10, `grow.py` sha256 d5960f4516b34bcb run unchanged, output `results/gr1-out.txt`, rows `results/gr1-rows.json`)
10 seeds, 3 needs, 6 arms, 3m47s on the laptop CPU, no model calls.

| Teacher | gate-signal | gate-random | nogate | fixed2 | fixed128 | fixed-same |
|---|---|---|---|---|---|---|
| 4, median test loss | 0.00089 | 0.00516 | 0.00545 | 0.02597 | 0.00482 | 0.00075 |
| 4, median width | 3 | 3 | 474 | 2 | 128 | 3 |
| 16, median test loss | 0.09556 | 0.09523 | 0.02517 | 0.09456 | 0.00621 | 0.09456 |
| 16, median width | 2 | 2 | 474 | 2 | 128 | 2 |
| 64, median test loss | 0.11819 | 0.10659 | 0.07069 | 0.12073 | 0.01547 | 0.11828 |
| 64, median width | 2 | 2 | 474 | 2 | 128 | 2 |

Guesses, judged as written:
- GR-a False. Median width was 3, 2, 2. The gated network did not grow to meet a larger need.
- GR-b False. `nogate` was worse than `gate-signal` on 1 of 3 needs (teacher 4 only). On teachers 16 and 64 the ungated
  network was better, because the gated one never grew at all.
- GR-c True (paired ratios 0.991, 1.001, 1.000). GR-d True (0.971, 1.000, 1.008). GR-e True (0.01547 against 0.11819).
  GR-c and GR-d are close to empty on teachers 16 and 64, since no arm grew there.

What it shows: both failure modes side by side. The gated colony starved (width 2, loss 15 times that of `fixed128` on teacher 16).
The ungated colony bloated (width 474 on every need, loss 6 times that of the gated one on teacher 4, 4 times that of `fixed128` on teacher 16).
Neither is restraint. The gate as built is a wall, not a judge.

Diagnostic (NOT preregistered, `gr1_diag.py`, output `results/gr1-diag-out.txt`): over 48 replayed trials on teachers 16 and 64,
the grown lineage's gate loss was 0.9859 to 1.0781 times the ungrown one (median 0.9992), and the gate needed below 0.98.
After the 300-step trial the child's input weights still had cosine 0.9945 (median) with its parent's.
Reading: a daughter that is a copy of its parent carries no new information, so the gate has nothing to see.
Same pattern at the agent layer: in E13 forced attempts won 4 of 19, and the `dfix1` maze daughter changed nothing
because the parent already held its idea. A lead, not a result.

## GR2 growth pilot: asymmetric division (guesses written 2026-11-10, after GR1, before any GR2 data)
Question: GR1's gate rejected all growth on the larger needs, and the diagnostic points at copy division.
Does the same gate judge well when the daughter differs from the parent?
One change from GR1: how a new neuron is born. Everything else (needs, data, seeds, budget, trial length, 2% gate,
doubling wait, charges) is `grow.py` unchanged. Code `razi-tools/cells/grow2.py`, written before any run.
- New neurons are born different: fresh input weights from the birth distribution, outgoing weight 0, so the
  network's output is unchanged at the moment of division and the parent is untouched. Same count as GR1 (half the width).
- `asym-signal`: 4 candidates per place are drawn blind, and the ones whose activity lines up best with the
  network's current error on the training rows are kept. Blind variation, then a signal picks.
- `asym-random`: the first candidates are kept without looking.
- `nogate-asym`: `asym-signal` growth with the gate always saying yes.
- Reference arms: `gate-signal` (GR1 copy division), `fixed128`, `fixed-same` (born at the width `asym-signal` reached).
- Reading the signal is charged one pass over the training rows at the size of the network plus all candidates.

Guesses:
- GR2-a: the median final width of `asym-signal` rises with the need: teacher 4 < teacher 16 < teacher 64.
- GR2-b: `asym-signal` beats copy division (`gate-signal`) on teachers 16 and 64, median paired loss ratio below 0.5 on both.
- GR2-c: restraint. On teacher 4 the median final width of `asym-signal` is 8 or less.
- GR2-d: `asym-signal` and `asym-random` are within 10% (median paired ratio 0.9 to 1.1) on at least 2 of 3 needs.
- GR2-e: `asym-signal` does not beat `fixed-same` by more than 10% on any need, and `fixed128` still beats it on teacher 64.
- GR2-f: `nogate-asym` has a higher median test loss than `asym-signal` on teacher 4.

### GR2 result (2026-11-10, `grow2.py` sha256 ba623d30e254388d run unchanged, output `results/gr2-out.txt`, rows `results/gr2-rows.json`)
10 seeds, 3 needs, 6 arms, 1m34s on the laptop CPU, no model calls.

| Teacher | asym-signal | asym-random | nogate-asym | gate-signal (copy) | fixed128 | fixed-same |
|---|---|---|---|---|---|---|
| 4, median test loss | 0.00091 | 0.00084 | 0.00322 | 0.00089 | 0.00482 | 0.00087 |
| 4, median width | 6 | 6 | 316 | 3 | 128 | 6 |
| 16, median test loss | 0.00229 | 0.00273 | 0.00527 | 0.09556 | 0.00621 | 0.00369 |
| 16, median width | 23.5 | 28 | 316 | 2 | 128 | 23.5 |
| 64, median test loss | 0.01430 | 0.01402 | 0.01788 | 0.11819 | 0.01547 | 0.01301 |
| 64, median width | 63 | 63 | 316 | 2 | 128 | 63 |

Guesses, judged as written:
- GR2-a True. Median width 6, 23.5, 63 for needs 4, 16, 64.
- GR2-b True. Paired loss ratio against copy division 0.024 (teacher 16) and 0.115 (teacher 64).
- GR2-c True. Median width 6 on teacher 4 (range 3 to 9).
- GR2-d True. Signal against random 1.098, 0.759, 0.915. Two of three inside 10%. On teacher 16 the signal arm was 24% better.
- GR2-e False, on both halves. The grown network beat a network born at the same width by 34.5% on teacher 16
  (ratio 0.655; 0.978 and 1.085 on the others), and it beat `fixed128` on teacher 64 by median (0.01430 against 0.01547).
- GR2-f True. Ungated growth 0.00322 against 0.00091 on teacher 4.

Reading (a lead from one toy problem, 10 seeds, not a result):
- The same gate that starved the colony in GR1 sized it to the need in GR2. The one change was that daughters are born different.
- Restraint and growth came from one rule. No arm was told how big to be.
- Ungated growth went to width 316 on every need and lost on every need (ratios 0.296, 0.425, 0.817).
- Blind proposals were about as good as signal-picked ones. The gate did the selecting. The gradient did the fitting.
- Not shown: that growth beats a well-chosen fixed size. `fixed-same` gets its width from the grown arm for free.
  The fair claim is that the gated colony found a good size without being told, at no loss against that size on 2 of 3 needs.
- Limits: tanh teacher-student regression, 8 inputs, one hidden layer, one learning rate, one margin, one trial length, numpy on CPU.

## GR3 robustness of GR2 (guesses written 2026-11-10, after GR2, before any GR3 data)
Question: does the GR2 picture (the gate sizes the network to the need, ungated growth bloats) survive when the knobs
I picked by hand are moved, and on a second kind of task? Code `razi-tools/cells/grow3.py`, written before any run,
imports `grow.py` and `grow2.py` unchanged.
- Six settings, one knob moved at a time from GR2: gate margin 0.005 and 0.08 (GR2 0.02), trial length 100 and 1000
  steps (GR2 300), learning rate 0.002 and 0.02 (GR2 0.005).
- Second task `sin`: the teacher is a sum of sine units instead of tanh units (needs 4, 16, 64), GR2 settings.
- Arms per setting: `asym-random` (blind proposals, GR2 showed the signal adds little), `nogate-asym`,
  `fixed-same` (born at the width `asym-random` reached). 10 seeds, same budget.

Guesses:
- GR3-a: median width of `asym-random` rises with the need (4 < 16 < 64) in at least 5 of the 6 settings.
- GR3-b: restraint holds: teacher 4 median width is 8 or less in at least 4 of the 6 settings. I expect margin 0.005 to break it.
- GR3-c: ungated growth has a higher median test loss than gated growth on teacher 4 in all 6 settings.
- GR3-d: on the `sin` task, width rises with the need and ungated growth is worse than gated on need 4.
- GR3-e: the GR2 surprise (grown beats a network born at the same width by more than 10% on teacher 16) repeats
  in at least 3 of the 6 settings.

### GR3 result (2026-11-10)
`grow3.py` (sha256 a11897170fb15172) run unchanged, 10 seeds, 7 settings, 3 arms, 630 rows, 3m41s, no model calls.
Output `results/gr3-out.txt` (sha256 1de5e7c66cd7fce6), rows `results/gr3-rows.json`. Medians over seeds.

| Setting | Gated width at need 4 / 16 / 64 | Gated / ungated loss 4 / 16 / 64 | Grown / born-same loss 4 / 16 / 64 | Ungated width |
|---|---|---|---|---|
| margin 0.005 | 13 / 52.5 / 141 | 0.269 / 0.549 / 0.809 | 0.651 / 0.604 / 0.993 | 474 |
| margin 0.08 | 4 / 13 / 23.5 | 0.152 / 0.568 / 1.351 | 1.004 / 0.910 / 1.114 | 474 |
| trial 100 | 9 / 19 / 52.5 | 0.131 / 0.215 / 0.367 | 0.903 / 0.943 / 0.994 | 1599 |
| trial 1000 | 4 / 19 / 63 | 0.177 / 0.563 / 1.162 | 0.776 / 0.739 / 1.196 | 141 |
| lr 0.002 | 9 / 19 / 63 | 0.218 / 0.251 / 0.735 | 0.976 / 0.923 / 1.162 | 474 |
| lr 0.02 | 6 / 28 / 94 | 0.103 / 0.207 / 0.568 | 1.130 / 0.827 / 1.003 | 474 |
| sin task | 7.5 / 23.5 / 4.5 | 0.851 / 0.906 / 1.402 | 1.086 / 0.924 / 1.015 | 474 |

Guesses, judged as written:
- GR3-a True. Width rises with the need in 6 of 6 settings.
- GR3-b False. Teacher 4 width is 8 or less in 3 of 6 settings, I guessed at least 4. Margin 0.005, trial 100 and
  lr 0.002 broke it (widths 13, 9, 9). I expected only margin 0.005 to break it.
- GR3-c True. Ungated growth is worse than gated on teacher 4 in 6 of 6 settings (ratios 0.10 to 0.27).
- GR3-d False on both halves. On the sin task width does not rise (7.5, 23.5, 4.5). Ungated is not worse on need 4 by
  the test the script applies (arm medians: gated 0.08847, ungated 0.07649). The paired ratio in the table (0.851) points
  the other way, so on sin need 4 the two arms are not separable.
- GR3-e True, at the edge. Grown beats born-same by more than 10% on teacher 16 in exactly 3 of 6 settings.

What holds: sizing to need (6 of 6) and the cost of ungated growth on a small need (6 of 6).
What does not hold:
- The exact amount of restraint depends on the knobs. A loose gate or a short trial lets a small need grow to 9 or 13.
  The order still holds, the size does not.
- A strict gate (margin 0.08) or a long trial (1000) under-grows the big need: gated is worse than ungated on teacher 64
  (1.351, 1.162). Restraint has a price when the need is large.
- The sin task at need 64 breaks the picture: median width 4.5, 3 of 10 seeds never won a trial.

Diagnostic, NOT preregistered (share of the clean target's variance left unexplained, medians): sin need 4: gated 0.22,
ungated 0.20, born-same 0.19. Need 16: 0.22, 0.26, 0.25. Need 64: gated 0.80, ungated 0.52, born-same 0.81.
So at sin need 64 nobody learns the task inside the budget, and the gated arm learns least. Reading: when a small step
of growth buys no measurable gain, the gate says no and the network stays small. The gate cannot tell "enough" from
"too hard to see progress yet". This is the same failure as GR1 (no visible signal, no growth), reached from the other side.

Status: pilot scale (toy network, laptop). Leads, not results.

## GR4 two ways to tell "satisfied" from "stuck" (guesses written 2026-11-10, after GR3, before any GR4 data)
Question. GR3 showed a fixed gate reads "one step of growth did not help" as "enough", and under-grows a hard need.
Two candidate laws fix this in different ways. Which one holds across easy, hard and noisy needs?
- Law `level` (a sensor): the network reads its own unmet need, u = gate loss / variance of the gate targets
  (the share left unexplained). The margin a growth step must clear is MARGIN * (1 - u / U0), U0 = 0.25. High need
  makes the gate loose, and above U0 growth is kept unless it is clearly worse. Low need makes it strict.
- Law `escal` (blind, by acting): the gate stays fixed. After each refused growth step the next step is twice as big
  (base step * 2^rejects, at most 16 times the base step). A kept step resets it. "No gain from a small step" is
  only believed after bigger steps also show none.
Same in all arms: blind candidates (GR2 `asym-random` rules), MARGIN 0.02, TRIAL 300, LR 0.005, budget 5,128,000,
10 seeds. `grow.py`, `grow2.py`, `grow3.py` imported unchanged.
Arms: `base` (GR2 fixed gate), `level`, `escal`, `nogate` (GR3 ungated blind growth).
Conditions (8): tanh teacher 4, 16, 64 (noise 0.1). Sin teacher 4, 16, 64 (noise 0.1). Noisy tanh teacher 4 and 16
(label noise 0.5). The noisy pair is a trap for `level`: the noise alone should keep u near U0, so the sensor reads
noise as need.
Outcomes. Test loss against the clean teacher (lower is better), final width, and regret: for each condition and seed,
an arm's test loss divided by the lowest test loss among the four arms. Medians over seeds.
Disclosure. I have seen all GR1 to GR3 data, including the sin shares (0.2, 0.2, 0.8). U0 was picked knowing them.
Guesses:
- GR4-a. On sin 64 both `level` and `escal` beat `base`: paired median loss ratio below 0.9 for each.
- GR4-b. Nothing is lost where the fixed gate worked. On tanh 4, 16, 64 the paired median ratio to `base` is inside
  0.8 to 1.25 for `level` on all 3, and for `escal` on at least 2 of 3.
- GR4-c. The trap works. On noisy tanh 4, `level` ends more than twice as wide as `base` (median width), and
  `escal` does not.
- GR4-d. `escal` has the lowest worst-case regret (largest median regret over the 8 conditions) of the four arms.
  Low confidence: `base` is already hard to beat on this measure.
- GR4-e. Under `escal` width still rises with need on tanh (4 < 16 < 64, median width).
Pilot scale. No model calls.

### GR4 result (2026-11-10)
Run: `grow4.py run results/gr4-rows.json --seeds 10 --par 8`, unchanged from the code written before the run
(sha256 a12329838d1faf3b, copy in `archive/grow4_v1_gr4.py`). 2m12s, 320 rows, no model calls. Output
`results/gr4-out.txt` (sha256 dc1cbcd8f8ddef50). Every arm spent between 5,125,922 and 5,128,000 units.

| cond | width base/level/escal/nogate | test loss base/level/escal/nogate | level/base | escal/base | regret base/level/escal/nogate |
|---|---|---|---|---|---|
| tanh4 | 6 / 6 / 6 / 474 | 0.00084 / 0.00084 / 0.00087 / 0.00505 | 1.000 | 1.048 | 1.00 / 1.00 / 1.05 / 6.15 |
| tanh16 | 28 / 28 / 25 / 474 | 0.00273 / 0.00261 / 0.00251 / 0.00520 | 1.000 | 0.983 | 1.09 / 1.02 / 1.00 / 2.02 |
| tanh64 | 63 / 78.5 / 77.5 / 474 | 0.01402 / 0.01370 / 0.01376 / 0.01659 | 1.000 | 1.025 | 1.00 / 1.00 / 1.04 / 1.27 |
| sin4 | 7.5 / 35 / 36 / 474 | 0.08847 / 0.02451 / 0.03447 / 0.07649 | 0.418 | 0.465 | 3.02 / 1.00 / 1.21 / 3.45 |
| sin16 | 23.5 / 94 / 84.5 / 474 | 0.13347 / 0.11622 / 0.11573 / 0.14434 | 0.956 | 1.001 | 1.09 / 1.06 / 1.08 / 1.26 |
| sin64 | 4.5 / 211 / 104 / 474 | 0.38187 / 0.29370 / 0.30976 / 0.28010 | 0.780 | 0.797 | 1.42 / 1.04 / 1.09 / 1.00 |
| noisy4 | 3.5 / 30.5 / 4 / 474 | 0.00804 / 0.05281 / 0.01225 / 0.08859 | 6.670 | 1.236 | 1.06 / 6.67 / 1.42 / 11.95 |
| noisy16 | 9 / 94 / 9 / 474 | 0.03849 / 0.08852 / 0.04160 / 0.10195 | 2.061 | 1.001 | 1.01 / 2.18 / 1.01 / 2.92 |

Worst-case median regret: base 3.02, level 6.67, escal 1.42, nogate 11.95.

Guesses, judged as written by the script (5 of 5 held):
- GR4-a True. On sin 64 both laws beat the fixed gate: ratios 0.780 (`level`) and 0.797 (`escal`).
- GR4-b True. Nothing lost on tanh: `level` 1.000, 1.000, 1.000. `escal` 1.048, 0.983, 1.025.
- GR4-c True. The trap worked. Noisy 4: width base 3.5, `level` 30.5, `escal` 4. The sensor read label noise as unmet
  need, grew about 9 times too wide and lost 6.7 times the loss. On noisy 16 the same: width 94 against 9, loss 2.06 times.
- GR4-d True. `escal` has the lowest worst-case regret, 1.42. Its worst condition is noisy 4.
- GR4-e True. `escal` width still rises with need on tanh: 6, 25, 77.5.

Diagnostic, NOT preregistered (per-seed view of `results/gr4-rows.json`):
- Seeds out of 10 where the arm had lower test loss than `base`: sin4 level 8, escal 8. sin16 level 7, escal 5.
  sin64 level 8, escal 7, nogate 9. noisy4 level 1, escal 4. noisy16 level 0, escal 5.
- On tanh `level` is the same network as `base` on 9, 7 and 5 seeds of 10 (need 4, 16, 64): where the need is nearly
  met the sensor changes nothing.
- Median kept growth steps base/level/escal: sin64 2 / 12 / 4.5. noisy4 1.5 / 7 / 1.
- `escal` width range over seeds is wide: tanh4 4 to 54, sin4 13 to 217. A doubled step that happens to pass the gate
  is kept whole, so single seeds overshoot. The median hides this.
- On sin 64 the ungated arm has the lowest median loss of all four (0.28010). When the need is far beyond reach, restraint
  costs. Neither law reaches it: `level` 1.04 and `escal` 1.09 times the best.

Reading.
1. The blind spot found in GR3 is real and both laws remove most of it. On the two sin needs where the fixed gate got
   stuck (4 and 64) both laws cut the loss by 20 to 58%.
2. The two laws fail differently. The sensor is best when its reading is true (sin 4, sin 64) and worst of all gated arms
   when it is not (noise read as need). The acting law is never best by much and never bad: it does not read need, it
   tests whether a bigger step shows a gain, and noise shows none at any step size.
3. So a sensor of unmet need is only as good as its ability to tell reducible error from irreducible error. From inside,
   one reading cannot tell them apart. Acting can: irreducible error does not move when you grow.
4. Status: pilot scale (toy network, laptop). Leads, not results. One hand-picked U0 (chosen after seeing GR3 shares) and
   one escalation rule. Not yet moved knob by knob as GR3 did for GR2.
