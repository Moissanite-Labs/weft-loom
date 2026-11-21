# Preregistration: exact amounts in repair, trained at a fixed cap

Status: registered by the commit that adds this file to the repository. No model has been trained, sampled or scored. A paid run starts only after the owner approves that run. Every number or setting marked (choice) is a decision made while drafting. Every number marked (measurement) was counted from real files by a script in this folder. Every number marked (arithmetic) follows from stated inputs.
A statement marked (expected) is a belief that no script here checks.

## Question

When a model must repair a rejected answer to a rational difference-constraint puzzle, and it may answer only with the repaired assignment under one small token cap, does training on feedback that gives the exact amount of each violation let it repair more often than training on feedback that names only the violated constraints?

## Why this run

The finished experiment tested the same idea without training and did not support it. Its main confound was that one model escaped into long open reasoning, which the other arms could not use equally. Here every arm answers under the same cap with answer text only, and training gives each arm the chance to learn to use its own feedback.

## Model and training

- Model: thinkingmachines/Inkling-2-Mini on the Tinker service, LoRA only.
- LoRA rank 8 (choice). The train_mlp, train_attn and train_unembed switches all on (choice, the library default).
- One epoch of plain cross-entropy on the target, loss on the target tokens only. Batch 32 (choice), so 64 steps per adapter (arithmetic from 2048 examples).
- AdamW, learning rate 1e-3 (choice, taken from an earlier smoke script and not tuned).
- Two training seeds (choice). Each trains its own three adapters, one per trained text.
- Chat layout: role and end markers are special tokens, not text. Prompts and targets are built by codec.py and checked id for id against the tml_renderers Inkling2 renderer (measurement, tests/test_layout_real.py). The target is the model's whole turn: its opening, the reply and the end marker.
- System line: `Thinking effort level: 0`, the text the renderer writes for effort 0.0 (choice). The model card says minimum effort does not fully disable reasoning, so the cap below is the control.
- Sampling: greedy, temperature 0.0, one sample per episode (choice).
- Stop tokens: both end_message and content_model_end_sampling (choice). The renderer's own stop is content_model_end_sampling alone. Stopping on end_message as well ends the reply at the end of the model's message.

## Texts

All texts follow the same puzzle, the same failed attempt and the same first message. They differ in what follows the failed attempt.

- A: the verdict only.
- B: the verdict and the violated constraints with their places.
- C: B plus an exact amount for each listed constraint, under one neutral label with no sentence that defines its sign. For example `(s +1/2)`.
- E: the same format as C, with the amounts of another puzzle that has the same number of violations. Only the pairing with the truth is broken, so E looks like C: every amount is positive and of similar size (mean 1.466 against 1.412 in the training set, about 4 percent apart, measurement).
- N: the amounts of C with the sign flipped, written `(s -1/2)`.

Adapters are trained on A, B and C only. E and N are test-time controls. Only violated constraints are listed, so every true amount is positive: the text C shows "+" in all 2048 training episodes and N is C with "+" changed to "-" in all of them (measurement, a test checks it). An adapter trained on N would only relabel C, so N is not trained.

The sign and value controls are done by showing the C adapter the texts E, N and B on the same episodes (paired), which is the only place where the amount can be wrong while the adapter has learned to rely on it.

## Training target

One canonical repair is the target in every arm, so the arms differ only in what they can see. It is built from the failed attempt and the exact checker, never from the planted point unless nothing else works:

1. A variable that every violated constraint names, moved the right way by the largest true excess, if the checker accepts it. A variable named first in every violated constraint comes before one named second, then the lower index. So a text that lists `x1 - x3` has the target lower x1.
2. Else the passing one- or two-variable move of smallest total size, each step being one of the true excesses. A step lowers the first-named variable of a violated constraint by its excess, or raises the second-named one by it. Moves are tried by total size, then fewer variables, then by their (variable, step) pairs in increasing order: lower variable index first, then the more negative step.
Pairs never move one variable twice. The first passing move in that order is the target (choice, the tie-break).
3. Else the planted solution.

In the training set the rules give 1450, 491 and 107 of 2048 targets (71 percent, 24 percent and 5 percent, measurement). Rule 2 has a tie in its first place, another passing move of the same total size that gives a different repaired answer, in 159 of the 491 training episodes where it fires, 90 of 259 in the first held-out set and 73 of 244 in the second (measurement, checks/rule2_ties.py).
The order above decides these, and a different order would give a different target in those episodes. The order uses only the roles of the violated constraints, which every text shows, so it gives no arm information that another arm lacks. The planted point alone, which an earlier draft used, equals a repair that C can reproduce in only 557 of 2048 episodes (a reviewer's count).

## Mechanism and what it predicts

The cheap rule for C is: move the variable shared by all violated constraints by the largest amount. It is exact when one variable was moved (440 of 440 episodes in the first held-out set, measurement).

It is partial when two were moved: it applies and passes in 251 of 560 episodes of the first held-out set, a small search finds the repair in 259 more, and 50 need the planted point. A rule of one subtraction per violated constraint passes only 476 of 1000 episodes there, so it is not the mechanism.

From B the same excess is two subtractions away (the attempt's values give x_u - x_w - c), so B asks for a little more arithmetic, not a full recomputation. The gap between C and B may therefore be small. This is a prediction, not a result.

## Arms of the test and predictions

The predicted order for adapters on their own text is C above B and B above A (prediction). For the C adapter shown other texts on the same episodes: C text above E text, C text above N text, C text above B text (prediction). N is expected to hurt most if the adapter uses the sign. If it uses the size only, N will match C, and the report says that.
These three comparisons are interpretive readings. They are not part of the decision rule below and cannot change its verdict.

### Chance floor on text E

An adapter that applies the largest-excess rule mechanically to the amounts text E shows still passes some episodes, because an overshoot often stays inside the constraints' slack. On the first held-out set (1000 episodes, exact enumeration, checks/e_floor.py):

| Rule applied to | Mechanical (first variable in order) | With the checker's look-ahead (first variable that passes) |
|---|---|---|
| E's amounts | 207 of 1000 | 264 of 1000 |
| the true amounts (text C) | 574 of 1000 | 691 of 1000 |

E's amounts equal the true amounts, in order, in 53 episodes, as a multiset in 58 and in their largest in 95. Of 1864 single amounts, 190 match. By number of violations the mechanical rule on E passes 116 of 420 (one violation), 71 of 362 (two), 19 of 166 (three), 1 of 39 (four), 0 of 13 (five or six).

So a C adapter that reads the values and applies the rule, but is shown the wrong values, should score near 21 to 26 percent on E, and one that does not apply the rule at all should score below that. A score on E between zero and about 26 percent does not show that the adapter ignores the values. The floor is exact for the first held-out set only. For the second it is not computed.

## Sizes and seeds

| Item | Value | Kind |
|---|---|---|
| Training episodes per adapter | 2048, half tier S and half tier M | choice |
| Training seeds | 300000 to 301023 (S) and 350000 to 351023 (M) | choice |
| First held-out set | 500 S and 500 M, seeds 400000 to 400499 and 450000 to 450499 | choice |
| Second held-out set | 500 S and 500 M, seeds 500000 to 500499 and 550000 to 550499 | choice |
| Pilot training | 256 examples in text C only, 128 S and 128 M, seeds 302000 to 302127 and 352000 to 352127 | choice |
| Pilot evaluation | 50 S and 50 M from training-range seeds 310000 to 310049 and 360000 to 360049 | choice |

All sets are disjoint from the registered ranges 100000 to 100099 and 200000 to 200099 of the earlier experiment, and the episode builder refuses any seed outside the range of its kind and tier. The pilot's training seeds lie above the first 1024 seeds of each tier that the full run trains on, so the pilot shares no episode with the full run (a test checks it).

The same episodes are used in every comparison, so comparisons are paired. The text E draws its amounts from decoy puzzles at seeds 700000 and up, outside every range above.

## Compute cap

Every reply is capped at 96 tokens (choice) and every comparison uses the same cap. The turn opening and the end marker do not count against the cap. A reply must be the answer only, one line per variable, with decimals and fractions read as exact rationals, and an optional leading plus sign is allowed. A reply that breaks the format is counted as its own outcome and is not a failed repair.
A reply that had to be cut at the cap is counted as a format break even if the cut text still parses, because the cut can land inside the last number and leave a different but valid value (it is stored with a cut flag, and the cut replies are counted).

## Primary comparison and the decision rule

The adapter trained on C, shown text C, against the adapter trained on B, shown text B, on the same episodes. Each test is the exact one-sided paired sign test on the episodes where exactly one of the two passes, at alpha 1/40 (choice). The claim is supported only if every item below holds. Each item is a separate test at 1/40, all of them are required, so no alpha is split.

1. C beats B on pass rate over all episodes of the first held-out set, for both training seeds.
2. The same test on the stratum where neither adapter broke the format, for both seeds. When item 1 holds and item 2 does not, the result is reported as not supported: the stratum governs.
3. B does not beat C on staying in the format, tested at 1/40 in the direction that C breaks the format more often, for both seeds. This is a no-harm gate. Failing to reach 1/40 does not show that the two break the format equally often.
4. Items 1 to 3 hold on the second held-out set for training seed 0, chosen before looking.

The second held-out set is touched only if items 1 to 3 hold for both seeds on the first set.

### When a comparison cannot test the claim

Items 1 and 2 count only if the comparison can test the claim (choice, as in the earlier plan). It can when both of these hold:

- there are at least 10 discordant episodes (episodes where exactly one of the two adapters passes), and
- neither adapter passes 5 percent or fewer, or 95 percent or more, of the episodes of the set.

Otherwise the verdict for that seed and set is `cannot_test`, which is not `not_supported`: the set could not show a difference whatever the truth is. Item 3 is a no-harm gate and has no such condition. In the code these are `GATES` in driver.py, and `judge` gives one verdict per seed and set:

1. Item 1 first. Not testable gives `cannot_test`. Testable and not won gives `not_supported`.
2. Item 2 the same way.
3. Item 3: if C breaks the format more often at 1/40, `not_supported`.
4. Otherwise `support`.

The overall verdict is `support` only if every seed and set that was run gives `support`. It is `not_supported` if any testable item failed. It is `cannot_test` only when no testable item failed and at least one could not be tested. When item 2 cannot be tested because few episodes are in the stratum, the result is `cannot_test` and not support, even if item 1 holds.

### The E, N and B controls

The C adapter on texts E, N and B (and C on its own text) is read, never decided on. For each the report gives whether the C text beats that text at 1/40 on the paired sign test, as a description. No result there changes the verdict. A C adapter that scores as well on E as on C is reported as possibly not using the values, and the primary claim is judged on items 1 to 4 alone.

## Power

Power is the exact probability that the first adapter wins the test of item 1, from the multinomial law over the three states of an episode: only C passes, only B passes, no difference (power.py, exact fractions). A second checker with scipy, sharing no code, agrees to 0.000035 (measurement). The table is for 1000 paired episodes, alpha 1/40, at least 10 discordant episodes.

The last column is the approximate power of items 1 and 4 together for both seeds and the confirmation, taken as the cube of the single power. This assumes independence. The same adapter is tested on both sets, so the tests are expected to be positively associated and the true figure to be somewhat higher than the cube (expected, not computed).
The single-test column is a strict upper bound for the whole rule, because the rule needs every item to hold. Items 2 and 3 can only lower it.

| Discordant episodes | Net effect | One test | Whole rule (approximate) |
|---|---|---|---|
| 15% | 2 points | 0.3423 | 0.0401 |
| 15% | 3 points | 0.6625 | 0.2908 |
| 15% | 4 points | 0.8953 | 0.7177 |
| 15% | 5 points | 0.9824 | 0.9481 |
| 25% | 3 points | 0.4513 | 0.0919 |
| 25% | 4 points | 0.6968 | 0.3383 |
| 25% | 5 points | 0.8763 | 0.6729 |
| 25% | 6 points | 0.9643 | 0.8968 |
| 35% | 4 points | 0.5510 | 0.1673 |
| 35% | 5 points | 0.7475 | 0.4177 |
| 35% | 6 points | 0.8864 | 0.6964 |
| 35% | 8 points | 0.9892 | 0.9680 |

The share of discordant episodes is not known before the run. The smallest net effect for which the whole rule (the cube above) has power at least 0.8 is 4.5 points at 15 percent discordant, 5.5 points at 25 percent and 6.5 points at 35 percent (arithmetic, printed by power.py with half-point steps).
A smaller true effect is mostly missed, so a result of "not supported" is not evidence that no smaller effect exists.

At 400 episodes per set, an earlier size, a 5-point effect at 15 percent had power 0.35 for the whole rule. The sets are larger for that reason (choice). The cost of the larger sets is small, but sampling is one call per episode, so the pilot measures the time per call before the full run is started.

## What counts against the hypothesis

- C does not beat B under the decision rule. The result is reported as not supported.
- B matches or beats C.
- The comparison cannot test the claim: fewer than 10 discordant pairs, or an adapter at 5 percent or below, or 95 percent or above (choice, as in the earlier plan). The report says `cannot_test`, and does not call this support or evidence against.

A result against the claim is reported with the same weight as one for it.

Not part of the verdict, reported as interpretation (see the controls above): the C adapter passing as often on text E as on text C (it may not use the values, and part of any gain over B may come from reading that a number is present), and passing as often on text N as on text C (it may not use the sign).

## Co-primary outcome: format breaks

The share of replies that break the format is reported for every adapter and text, next to the pass rate. The decision rule above fixes its direction (item 3), its stratum (item 2) and what happens when the all-episodes test and the stratum test disagree. The stratum is fixed here so that an adapter cannot win by leaving the format less often than another.

## Exploratory

These are one of many looks and are not findings.

- Tier S against tier M.
- A against B.
- The untrained model on each of the five texts, as a baseline for what training added.
- Learning curves over the 64 steps, if loss is logged.
- Whether the repaired answer moves the summed violation down when it does not pass.
- Any effect of LoRA rank.

## Stopping rule

Each adapter trains for the fixed 64 steps with no early stopping and no look at either held-out set during training. The second held-out set is touched once for this decision, under the registered decision id primary-c-vs-b-seed0-confirm (decisions.json, sha256 209f953163eb70e072c1f9d89f3c13adbc37572be340a76a8ab0f489098131e6).

The touch is recorded before any evaluation, as a receipt in the hash chain and as a line in the latch file. It names the four evaluations it covers, and its token covers those four only, once each. A second touch for the same decision id is refused if either the chain or the latch file holds one, so a new latch path or a deleted latch file does not buy a second touch.
One limit remains: a new chain together with a new latch file is a new experiment, and nothing in the files can tell. The head of the chain is pinned in memory within a process and can be passed in to a new process.

Before the touch the code checks that the ceiling left covers the four set-2 evaluations at their upper bounds (the prompts and the full cap plus overhead sampled for every reply), so that running out of budget cannot lose the one touch part way through.
If spending reaches the ceiling, the run stops before the call that would reach it, the report says it is incomplete, and no decision is made from partial results.

The spend is kept in an append-only ledger, written and flushed to disk before each call and settled after it. A new process for the same run id reads the ledger and counts all earlier spend against the ceiling.
A run id that has already started refuses to start again unless the owner asks for a resume, the plan must be the same plan (a hash of the whole plan is stored), a restart runs the plan again from the start, and the whole plan must fit under what is left of the ceiling. A service that returns more tokens than the limit asked for is counted in full and then stops the run.
The ceiling is therefore a total for the run id across restarts. The approvals file and the ledger belong to the owner's write area in a real run, and the code cannot enforce that.

## Spend

| Item | Tokens | Dollars | Kind |
|---|---|---|---|
| Pilot (one adapter, 256 examples, base model and adapter on 100 episodes each) | 184,306 | 0.0926 | tokens counted with the local tokenizer, dollars arithmetic at the published prices |
| Full plan (three trained texts, 2048 examples, two seeds, both held-out sets, controls) | 13,385,972 | 5.3793 | same |
| Pilot ceiling | | 0.50 | choice |
| Full run ceiling | | 12.00 | choice |

The exact full-plan cost is 26896611/5000000 dollars (arithmetic). Prices are the published rates for the 64K context: 0.75 dollars per million training tokens, 0.15 per million prefill tokens and 0.50 per million sampled tokens.

The sampling figure assumes the full cap plus the turn opening and the end marker is sampled for every reply, so it is an upper bound. The meter counts the tokens a call returns, not the cap. The token counts use the tokenizer carried by tml_renderers, and whether it matches the Mini model is not verified.

The pilot has one job. It checks the chat layout, the tokenizer, the step time, the time per sampling call and the format-break rate before any larger spend. Its results are not part of the registered result and its episodes are not reused.

The pilot has its own run id, its own ceiling and its own code path (run_pilot in driver.py): a run started for the pilot plan cannot run the full plan, and the reverse. It trains one adapter on text C, evaluates the untrained model and the adapter on the pilot's 100 evaluation episodes (training-range seeds, never a held-out set) in text C, and writes its measurements as one receipt.
Its gates, all required for a go (choices):

| Gate | Pass if |
|---|---|
| Layout | at least 95 percent of the 200 sampled replies begin with the model's own turn opening, which the prompt leaves for the model to write |
| Format | the adapter breaks the format in 20 percent or fewer of its 100 replies |
| Testable | the adapter's pass rate on the 100 episodes is above 5 percent and below 95 percent |
| Time | the sampling time per call times the 21,000 calls of the full plan, plus the step time times its 384 steps, is at most 12 hours |

The call and step counts come from the plan (driver.plan_calls). The offline layout check against the renderer is a separate test and does not replace the first gate, which measures what the service does.

## Gates

The loop runs under the five gates of the ratchet: the harness locked by hash (including the registry of decision ids), receipts chained and float-free with every decided result matched to a receipt and its counts recomputed.

The other three: a candidate identical to the baseline rejected, the second held-out set touched once per registered decision with a token that covers only the named evaluations, and one cap for every comparison.

The exact checker is the only judge. The paid backend refuses to start without an approval for this exact run id and a plan that names training, prefill and sampling under the ceiling, and a run is tied to one plan.

Every reply is stored whole, with its episode id and cut flag, in a replies file beside the chain, and the receipt names it by hash. Before any decision the replies are rescored with the exact checker on episodes rebuilt from their seeds, and the counts must match. A result that no evaluation produced cannot be decided on unless replies exist that give it.
Invented replies would still pass this check, and the check proves only that the recorded outcomes follow from the recorded replies.

The approvals file is written by the owner outside the agent's write area, with the run id and the ceiling.

## Revision notes

Changes made to this draft after an independent review on 2026-11-21, before any registration:

- N and E moved from trained arms to test-time controls on the C adapter, because N is C relabelled.
- Prompts and targets built with special tokens through the renderer layout instead of literal marker text.
- One canonical repair as the target in every arm.
- The mechanism restated as the largest-excess rule, with measured coverage.
- Power computed, held-out sets enlarged from 400 to 1000 episodes each.
- Decision rule written out for the format outcome, the stratum and the second set.
- Pilot training seeds moved out of the full training range.

Changes made after a second independent review on 2026-11-21, before any registration:

- The spend ceiling now holds across restarts: an append-only ledger written before each call, a restart needs an explicit resume, the same plan and room under what is left. The stopping rule text was rewritten to say so.
- A run is tied to one plan by a hash. The pilot has its own code path, run id and ceiling, and gates with thresholds. The one touch of the second set is protected by a headroom check against the remaining ceiling.
- The decision rule in the code now has the 10-discordant and 5 and 95 percent conditions, and the verdict `cannot_test` apart from `not_supported`. The E, N and B controls are labelled interpretive and cannot change the verdict.
- The chance floor of the C adapter on text E is stated (207 and 264 of 1000), with a script.
- A touch is a receipt in the chain, and the registry is read from the hashed file by both the latch and the evaluation. Raw replies are stored and rescored before any decision. The chain head is pinned within a process.
- A reply cut at the cap counts as a format break.
- Choices now marked: sampling temperature, the system line, the stop tokens, the tie-break in rule 2 (now written out, with its tie counts). The dependence statement for the whole-rule power is labelled expected. The minimal detectable effects are printed by code. The wording about E's amounts is "similar size". The C adapter on text B moved from the exploratory list to the interpretive controls.

## Statement

No result exists yet. This file was written before any model was trained or evaluated in this loop. Later changes go in a dated amendments section at the end and never replace the text above it.
