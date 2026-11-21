# Outside check of a post-hoc study of the Qwen logs

Another team studied this record's mid-size model logs after the fact and published the study as draft pull request 42 on this repository. It reads the same logs that are in `results/`. This folder holds our check of it. Nothing here changes the registered result.

Every number below is printed by `check_pr42.py`, which reads the four logs in `results/`. The script and its controls are in this folder.

## How the check was done

Two passes, by different agents of our team. The first pass (the evaluator) tried to narrow each claim. The second pass (the advocate) argued the other team's side as hard as the data allowed, then ruled. Where the two differ, the advocate's ruling is the one recorded here.

The evaluator and the advocate each wrote two checkers that share no code with each other or with the other team's script. Their counts agree with each other and with `check_pr42.py`, which was written afterwards and shares no code with them. No model was rerun.

Kinds of evidence used below:

- **exact**: integer or fraction arithmetic over the whole stated scope. Every sign test is the one-sided binomial test on discordant pairs, unless the text says two-sided.
- **sampled**: a label-swap correction with a fixed seed. Each draw is exact, the number of draws is finite.
- **heuristic**: exact arithmetic on a definition that is itself a judgment. The lenient reading of a reply is one.

## What their study claims

All claims are about the mid-size model, Qwen3.8-27B-AD-Q4_K_M, on tier S unless a tier is named.

1. Replacing the signed amount with its negative (arm D against C) makes the model write a long open-reasoning reply in round 2 that breaks the answer format. They attribute it to a message that contradicts itself.
2. Among passes with no unreadable round, C beats D. Their windows are cumulative reply times of 15 to 45 seconds.
3. In round 2 alone, C passes where D does not more often than the reverse.
4. After four rounds D beats C, which they call a complete sign reversal.
5. Together these form a two-channel Simpson's paradox.
6. D costs about 1.7 times the reply time of C.
7. Among instances readable in round 2 in both arms, the true amounts do not shrink the summed excess more than the flipped ones.

## What reproduces

Every count in their part on this data reproduces, on two independent checkers and again on `check_pr42.py`. The main counts on tier S, then tier M where it matters:

| Claim | Count printed by `check_pr42.py` |
|---|---|
| Passes within four rounds, A, B, C, D | 65, 75, 69, 77 on S. 2, 8, 7, 12 on M |
| Round 2 unreadable, D only against C only | 20 against 0 on S. 17 against 1 on M |
| Passes with no unreadable round, C only against D only | 15 against 3 on S. 2 against 0 on M |
| Round 2 passes, C only against D only | 9 against 2 on S. 0 against 0 on M |
| Four-round passes, D only against C only | 11 against 3 on S. 8 against 3 on M |
| Total reply seconds, D over C | 1.736 on S. 1.441 on M |
| Summed excess in round 2, C below D against D below C | 3 against 4 on 45 instances on S. 13 against 6 on 69 on M |

Their other counts also match: the survival counts at each time budget, the crossing at 90 seconds (C only 8, D only 10), and the split of the C minus D difference into +12 and -20 on tier S. The round-by-round verdicts in the logs were rebuilt from the prompts and replies by the recount in this record, with no disagreement.

What does not reproduce is a label, not a number. One line in their script is called a negative control but builds no synthetic data. It asserts the observed value.

Their figures on the 45 and 69 shared instances are not computed in their script. They reproduce under the definition their text implies. Their 67.7% against 66.7% are rates in each arm, not on the shared 45.

## Their claims after both passes

| Finding | Ruling after both passes | Strongest surviving claim | Evidence |
|---|---|---|---|
| C beats D with no unreadable round (15 against 3) | Stands | On Qwen tier S, C produced more solves without any open-reasoning round than D (15 against 3, one-sided adjusted p about 0.009), because D's flipped sign sent the model into long open-reasoning rounds that usually held the right answer in the wrong format. Among the 66 instances where neither arm left the format, C and D solved 44 and 43. | exact, sampled for the adjustment |
| Two-channel Simpson's paradox | Stands as a rejection of the name | The C minus D difference splits into +12 of 100 from passes with no unreadable round and -20 of 100 from passes after one. This is an effect mediated by open-reasoning rounds. It is not Simpson's paradox. | exact |
| Post-hoc windows and the round 2 and four-round claims | Stands, narrowed | After one-sided correction over 13 C-over-D statistics, C beats D among no-unreadable passes (15 against 3). D gains more late passes than C (20 against 0). The round 2 advantage (9 against 2) and an unbounded D lead (11 against 3, two-sided p 0.057) are not established. | exact, sampled |
| The flipped sign triggers the escapes | Stands, narrowed | Flipping the sign (C to D) raised round 2 open-reasoning replies from 0 to 20 discordant instances on S and from 1 to 17 on M. Whether the sign or the self-contradiction does it is not separated, and D's excess over the no-amount arm B is not shown on either tier (16 against 10 on S, p 0.16. 20 against 11 on M, p 0.075). | exact |
| Tier scope | Stands, narrowed | The escape effect holds on each tier. The 15-against-3, 9-against-2 and 11-against-3 counts are tier S results (on M: 2 against 0, 0 against 0, 8 against 3). | exact |
| Verification claims in their script | Stands, narrowed | Its real checks (round-1 identity, recount match, permutation nulls, type guards) are sound. It lacks any check that could fail if the headline claims were false. Pinning observed outputs is fine, and this record does it too. | quoted from the script |
| Transfer to the small model | Falls as a narrowing | On the small model, where the open channel is closed by design, the plain count favours the true sign (16 against 4) and no reversal appears. This is what their two-channel reading predicts. The test family leaves the fast-channel test unreplicated and says nothing against their claims about Qwen. | exact |

On the Simpson label. A reversal needs the same direction inside every stratum and the opposite direction overall. Split by whether an arm had an unreadable round, D's pass rate is at least C's in both strata and overall on tier S.

The counts are 56 of 86 against 44 of 67 with no unreadable round, 13 of 14 against 33 of 33 after one, and 69 against 77 overall. The +12 is a difference in counts over strata of different sizes, not a difference in rates. Nothing reverses.

The split variable is also caused by the arm, so it is a mediator and not a background covariate. We make no Simpson claim of our own.

The advocate added that in a paired design with the same instances in both arms, no reversal over a split fixed before the arms differ can occur. The script prints this for the round-1 split: D is at least C in every group. The one real reversal in their data is across time budgets. C leads at 30 seconds (56 against 44) and D leads when unbounded (77 against 69). The curves cross near 90 seconds.

## Points in the other team's favour

- On tier S, in 7 of the 9 instances where C passed round 2 and D did not, D's unreadable round 2 reply already held a satisfying assignment under the lenient reading. All 9 passed in round 3. Scored in any format, round 2 solves are C only 5 against D only 14. That is a heuristic. It supports their view that D's cost is time more than failure.
- The time cost is real. On tier S, in those 9 instances D's round 2 reply took 54.5 to 86.0 seconds. C's took 2.9 to 3.6.
- The correction was stricter than needed. On tier S, their claims C over D are in the registered direction. With a one-sided label-swap correction (sampled) the 15-against-3 count is adjusted to about 0.008 to 0.009. The 60-second window gives about 0.024 to 0.025. Round 2 stays at about 0.08.
- The late passes show a budget effect on both tiers: D only 20 against C only 0 on S, and 8 against 1 on M.
- Their flipped-sign contrast holds on both tiers. The evaluator's replacement wording (C produced the fewest escapes of any arm) fails on M, where arm A has 10 and C has 14.
- The small model result is what their reading predicts. On tier S its readable replies took 20.4 to 21.9 seconds from the 10th to the 90th percentile in every arm on S. That narrow band fits a private reasoning budget used up in every round. Token counts were not logged, so this is an inference. If it holds, their escape claim could not show up on that model.
- The advocate noted that their own README already says the tier S gap in the excess measure is driven by C staying readable while D escapes into long reasoning.
- Their committed JSON already held the full sweep over eleven time budgets and the B over C escape count of 19 against 5 on tier S. The family was shown, not hidden.
- Their README table is labelled tier S. Only the pull request body and one script comment lack a tier label.
- Their script's real checks are sound: round-1 identity, a match against our recount, permutation nulls and type guards.
- The reading that D's flipped sign sets up a self-contradiction ("cognitive dissonance") is one our own README raised first.
- The 11 against 3 four-round count is our own registered check, not a window they picked.
- On the small model's tier M, the C below D count in round 2 summed excess is 54 against 25 (D below C), one-sided p 0.000733, a lead for a registered test.
- The never-escaper set is a true principal stratum here. Each instance's escape status is observed under both arms from the same round 1 reply, so restricting to it does not select on an outcome.

## Held-out test on the small model

Before any statistic was computed on the small model's logs, a plan was written and its hash recorded. The plan is `HELDOUT-PLAN.txt` in this folder, copied unchanged. Its SHA-256 is `d015dc129860e989cbfbde0b9769dc7e54e2cd42f9930638170234005623bab7`. It has a `.txt` extension because it is kept byte for byte, and the repository's prose rules for Markdown do not apply to a frozen record.

The hash was recorded in an internal team note that is not published. The plan file was made read-only at 18:59:45 UTC on 2026-11-21. That is not a public timestamp, and the note records no deviations from the plan. The plan's mentions of EVAL.md mean that note, its paths refer to the team's internal working copy, and the README it names is this record's `README.md`.

Not blind, and the plan says so. The record's README had already been read, so the four-round counts (tests G4 and G5) were known in advance. The round 2 escape test (G1) was only partly blind. Tests G2, G3, G6, G7, G8 and G9 were held out.

Our own check of their direct-repair statistic on the small model's tier M (54 against 25) was run after reading the evaluator's exploratory note on a related statistic, so it is not blind either. It is a lead for a registered test.

Results as printed by `check_pr42.py`. G1 to G4 use the plan's Holm step-down over 8 tests. G8 is secondary and shows its raw p.

| Test | Tier S | Tier M | Verdict by the plan |
|---|---|---|---|
| G1, round 2 unreadable, D over C | 1 against 2 | 0 against 0 | not replicated. After the advocate: not applicable, because PR 42 claims nothing about gemma |
| G2, pass with no unreadable round, C over D | 14 against 4, raw p 0.0154, Holm 0.124 | 4 against 2 | not replicated |
| G3, round 2 pass, C over D | 6 against 4 | 0 against 0 | not replicated |
| G4, four-round pass, D over C | 4 against 16, other-direction p 0.0059 | 2 against 4 | contradicted (not blind). After the advocate: not applicable, because PR 42 claims nothing about gemma |
| G8, neither arm unreadable, C over D | 12 against 4, p 0.038 | 4 against 2 | above the 0.025 line on S |

Secondary results the plan also named. G6, total seconds D over C on tier S, is 1.041. G7, passes within 30 seconds on tier S, are C 44 and D 44 with no discordant pairs. G5, the Simpson structure, and the scaled window T* are not computed by `check_pr42.py`, so they are not reported here. The plan's written predictions are in the plan file and are not restated.

The advocate's reading of this table. The plan's family held two tests with no discordant pairs, which can never reject. The verdict "not replicated" depends on that family and not only on the counts. Both alternative families were chosen after the result, so neither counts as a replication.

The small model's round 2 unreadable replies are decimal answers (A 10, B 5, C 4, D 3 on tier S, apart from one prose reply in A). No open reasoning appears. The plan's G1 and G6 could not detect the claimed mechanism in a model that has none.

## Limits

- No model was rerun. Times are the logged seconds. Reply stop reasons and token counts were not logged.
- The lenient reading takes the last number written for each variable anywhere in a reply. It may pick a trial value from the middle of the reasoning. A satisfying assignment is a valid answer either way, but the counts are a heuristic.
- The correction over time windows is sampled with a fixed seed. Two seeds are printed and agree within 0.002.
- One-sided tests in the registered direction were used for C over D. The direction of the four-round claim (D over C) is the opposite of the registered one, so its honest p is the two-sided 0.057 (tier S) and 0.227 (tier M).
- Temperature 0 gives one draw per instance. The escape effect is a per-instance deterministic effect and says nothing about the spread between runs.
- Tier M sits near the floor. No arm solved more than 12 of 100.
- The second part of their study, which uses other data, was not read.

## Rerun

From this folder, with no model:

```
python3 -I -B check_pr42.py
python3 -I -B check_pr42_controls.py
```

The same output comes from `-I -O -B` and from `-I -B -W error`. The controls feed the script synthetic logs. A log with identical arms must give no discordant pairs. A planted gap must be found. Logs with a missing arm, a duplicate round, a round gap or torn JSON must be refused.
