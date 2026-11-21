# Repair signal

## Question

When an exact checker rejects a model's answer, does telling the model the signed exact amount by which each constraint failed let it repair in fewer rounds than telling it only which constraint failed and where?

## Status

`complete`

The design is preregistered. Both registered runs are done and reported under Results. Neither model supports the claim. By the registered rule each model is "not decided".

Part of siliconcordat/.github#5.

## Preregistration

[PREREG.md](PREREG.md), committed before any registered run. It fixes the hypothesis, the four feedback arms, the sizes, the seeds, the paired test and the rule for what counts against the claim.

## How to rerun

Requirements: Python 3.10 or newer, standard library only. Run every command from this folder, `experiments/repair-signal-2026-11-20/`.

Check the harness (verified, no model needed):

```
python3 -O -B -W error -m unittest discover -s tests
python3 -O -B -W error selftest.py
python3 -I -B selftest.py
python3 mutate.py
```

The unit tests are in `tests/`, including `tests/test_decision_rule.py`, which pins the preregistered decision rule at each boundary. They run 59 tests. `mutate.py` applies 51 deliberate breaks, one at a time, and must report zero survivors. For each break it runs the unit tests, the self-test and `recount_controls.py`.

Run against a local server that speaks the OpenAI chat protocol, such as llama-server. Replace `NAME` with a label for the model. The `--model` value is sent to the server as the model name.

```
mkdir -p results
URL=http://127.0.0.1:8080/v1
python3 -B runner.py --url $URL --model NAME --tier S --base-seed 100000 --count 100 --k 4 --log results/NAME-S.jsonl
python3 -B runner.py --url $URL --model NAME --tier M --base-seed 200000 --count 100 --k 4 --log results/NAME-M.jsonl
python3 -B analyze.py results/NAME-S.jsonl results/NAME-M.jsonl --k 4
```

An interrupted run is resumed by running the same command again. Finished units are skipped and a torn last line is ignored. Set `RSIG_API_KEY` if the server wants a bearer token. The runner reads only the `content` field of the reply. Use a mode or template in which the model answers without a long reasoning preamble, or raise `--max-tokens`.

The registered run of the mid-size model used these commands, at harness commit 9ac6dbe3:

```
llama-server -m Qwen3.8-27B-AD-Q4_K_M.gguf --host 127.0.0.1 --port 8091 -np 1 -ngl 99 -c 8192 --reasoning off
M=Qwen3.8-27B-AD-Q4_K_M
URL=http://127.0.0.1:8091/v1
python3 -B runner.py --url $URL --model $M --tier S --base-seed 100000 --count 100 --k 4 --max-tokens 1024 --log results/$M-S.jsonl
python3 -B runner.py --url $URL --model $M --tier M --base-seed 200000 --count 100 --k 4 --max-tokens 1024 --log results/$M-M.jsonl
python3 -B analyze.py results/$M-S.jsonl results/$M-M.jsonl --k 4
```

It ran on one Apple M1 Max with 64 GB of memory, macOS 27.0.1, Python 3.14.6 and llama-server 0.5.0 (build 11146, commit 7fe450e19). The model file's SHA-256 is `9f21564b0c962fd397509672a4a6d11a008c6b80cc6573295bb562832492abf0`. The run is known to work on this one machine only. A different server build or machine may give different replies at temperature 0.

The registered run of the small model used the same machine, server build and runner, with the settings fixed in the plan:

```
llama-server -m gemma-4-E4B-it-Q8_0.gguf --host 127.0.0.1 --port 8091 -np 1 -ngl 99 -c 8192 --reasoning on --reasoning-budget 1000
M=gemma-4-E4B-it-Q8_0
python3 -B runner.py --url $URL --model $M --tier S --base-seed 100000 --count 100 --k 4 --max-tokens 1400 --log results/$M-S.jsonl
python3 -B runner.py --url $URL --model $M --tier M --base-seed 200000 --count 100 --k 4 --max-tokens 1400 --log results/$M-M.jsonl
python3 -B analyze.py results/$M-S.jsonl results/$M-M.jsonl --k 4
```

Its model file's SHA-256 is `f8854aa4480df62585a279e7ca0a881554fc18a41c59c4f62642d16a2ae47012`.

To check the committed logs without a model (verified, shown for the mid-size model, the same commands work for the small one):

```
python3 -B analyze.py results/Qwen3.8-27B-AD-Q4_K_M-S.jsonl results/Qwen3.8-27B-AD-Q4_K_M-M.jsonl --k 4
python3 -I -B recount.py results/Qwen3.8-27B-AD-Q4_K_M-S.jsonl results/Qwen3.8-27B-AD-Q4_K_M-M.jsonl
python3 -I -B recount_controls.py
```

The first command reproduces `results/Qwen3.8-27B-AD-Q4_K_M-analysis.txt` and the second reproduces `results/Qwen3.8-27B-AD-Q4_K_M-recount.txt`.

`recount.py` was written after the run and is not part of the registered analysis. It shares no code with the harness. It reads the constraints from the logged prompt, parses each reply with its own parser, rebuilds every verdict with exact fractions and stops on any disagreement with the log.

`recount_controls.py` feeds it seven corrupted copies of the mid-size model's tier S log and expects each to be refused. It also compares the recount's reply parser with the harness parser on 9,010 generated replies and on every reply in that log. The two must agree on each.

It also runs 19 tests in all. They include a pin of every number `recount.py` prints for both models' logs (`recount_golden.json`, which must match the committed `results/*-recount.txt` files), checks of the reply reader on lines that break one rule each, and one control for each guard in the reader of decimal answers.

The outside check described under Results has its own script and controls, which need no model:

```
python3 -I -B outside-check-pr42/check_pr42.py
python3 -I -B outside-check-pr42/check_pr42_controls.py
```

Each log line holds the prompt, the reply, hashes of the chat and the reply, the checker verdict and the violations. Nothing is sent anywhere except the chosen URL.

## Results

Both models have run. Each model is its own test and nothing is pooled.

- Mid-size model, Qwen3.8-27B-AD-Q4_K_M: 2026-11-20 18:17 UTC to 2026-11-21 01:33 UTC.
- Small model, gemma-4-E4B-it-Q8_0: 2026-11-21 01:36 UTC to 15:49 UTC.

Most numbers in the next four subsections are in the two `results/*-analysis.txt` files, the output of the registered `analyze.py`. The round 1 solves and the counts of identical first replies are in the two `results/*-recount.txt` files.

`recount.py` gets the same counts and sign-test p values from the raw prompts and replies. It does not compute the rounds-to-solve test.

### Verdict by the registered rule

| Model | Level | Solved by C and not B | Solved by B and not C | Sign test p, C over B | Verdict |
|---|---|---|---|---|---|
| mid-size | S | 7 | 13 | 0.942 | against |
| mid-size | M | 3 | 4 | 0.773 | cannot test: 7 discordant pairs, and the rule needs 10 |
| small | S | 6 | 5 | 0.500 | inconclusive |
| small | M | 7 | 7 | 0.605 | against |

For each model the rule gives "not decided" overall. No level of either model supports the claim.

### Solved within 4 rounds, of 100 instances

| Model | Level | A: verdict only | B: constraint and place | C: plus signed amount | D: sign flipped |
|---|---|---|---|---|---|
| mid-size | S | 65 | 75 | 69 | 77 |
| mid-size | M | 2 | 8 | 7 | 12 |
| small | S | 85 | 88 | 89 | 77 |
| small | M | 6 | 9 | 9 | 7 |

Round 1 solved 22 of 100 on S and none on M for the mid-size model, and 44 on S and 1 on M for the small model.

The plan says the first reply is the same in every arm. That held on all 200 instances for the mid-size model. For the small model it held on 99 of 100 instances on S and 95 of 100 on M. This is a departure from the plan.

The logs show that on all six, arm A got a different first reply and arms B, C and D got the same one. On each of them the first-round verdict was the same in every arm. So the test of C against B and the check of C against D are not touched. Only the check of B against A is: on M, B alone solved one of those instances.

Arm A is the first unit run for each instance. A likely cause is that the server's cache held a different earlier chat when arm A started. That is not tested.

### Checks

These are reported next to the verdict and do not change it.

- B against A, expected direction B at least as good. Mid-size: 20 solved by B alone against 10 on S (p 0.049), 7 against 1 on M (p 0.035). Small: 7 against 4 on S (p 0.274), 8 against 5 on M (p 0.291). The direction is as expected at all four.
- C against D, expected direction C better. Mid-size: 3 solved by C alone against 11 by D alone on S, 3 against 8 on M. The flipped-sign arm did better. Small: 16 against 4 on S (p 0.006), 4 against 2 on M (p 0.344). Here the true sign did better.

On tier S the small model solved fewer when told the wrong sign (16 against 4). That fits a model that reads the sign. It is one of eight checks, none with a registered threshold, and on tier M the counts are 4 against 2. The mid-size model shows no such drop. The next subsection but one gives a possible reason.

The flipped-sign arm differs in more than the direction. Its message calls each listed constraint violated and gives it a negative excess, while the note under it defines the excess as left side minus bound. So the message contradicts itself, and a drop in D may come from that as well as from the sign.

### Secondary measures

Reported and not used for the decision.

| Measure | Model | Level | A | B | C | D |
|---|---|---|---|---|---|---|
| Repeated identical answers, share of round pairs | mid-size | S | 0.46 | 0.08 | 0.09 | 0.06 |
| Repeated identical answers, share of round pairs | mid-size | M | 0.87 | 0.54 | 0.56 | 0.55 |
| Repeated identical answers, share of round pairs | small | S | 0.11 | 0.08 | 0.07 | 0.09 |
| Repeated identical answers, share of round pairs | small | M | 0.52 | 0.15 | 0.16 | 0.23 |
| Unreadable replies, share of rounds | mid-size | S | 0.15 | 0.10 | 0.05 | 0.12 |
| Unreadable replies, share of rounds | mid-size | M | 0.03 | 0.06 | 0.04 | 0.08 |
| Unreadable replies, share of rounds | small | S | 0.19 | 0.14 | 0.15 | 0.14 |
| Unreadable replies, share of rounds | small | M | under 0.01 | under 0.01 | under 0.01 | 0 |

Rounds to solve, C against B, paired sign-flip test: p 0.895 on S and 0.828 on M for the mid-size model, 0.612 on S and 0.500 on M for the small one.

The harness counts a repeat when two readable answers are equal, and also when two unreadable replies are the same text.

### What the logs show beyond the plan (not preregistered)

This subsection is description. It comes from reading the logs after the runs, it was not in the plan, and it tests nothing. Its numbers are in the `not_preregistered` part of the two `results/*-recount.txt` files.

**Mid-size model.** Almost every unreadable reply is the model reasoning in the open where the answer lines should be. The plan treated such a reply as a wasted round that gets the same message in every arm. In the run it worked as a round of thinking, because the reply stays in the chat and the next round can read it.

On tier S there were 117 unreadable replies, 116 of them in round 2.

- 75 end with a complete assignment, and in 74 of those the assignment satisfies every constraint. The model had found an answer and wrapped it in text the format forbids. The next round passed in all 75. So the strict format cost these units one round and not the solve.
- 42 stop without a final assignment. The next round still passed in 38 of the 41 that had a next round.
- An unreadable reply took a median of 79.6 seconds against 3.0 for a readable one. That fits replies running to the 1024-token cap. The logs do not record why a reply stopped.

| Mid-size model, tier S | A | B | C | D |
|---|---|---|---|---|
| Unreadable replies in round 2, of the 78 units unsolved after round 1 | 43 | 27 | 13 | 33 |
| The next round passes, after an unreadable round | 42 of 43 | 26 of 27 | 12 of 13 | 33 of 33 |
| The next round passes, after a readable failed round | 1 of 147 | 27 of 143 | 35 of 162 | 22 of 137 |

On tier S, 113 of the 198 passes after round 1 came straight after an unreadable reply. Tier M is different. Of its 77 unreadable replies only 1 ends with a complete assignment, and the next round passed after 16 of the 77. Another 13 passes followed a readable failed round, out of 1105 such rounds.

So for this model the arm totals mix two effects: repair from the feedback text, and how often each kind of feedback led the model to reason in the open. On tier S the model did that least often in C and most often in A. On tier M the order is different, as the next subsection shows. The registered verdict stands as registered. It does not separate the two effects.

**Small model.** This side channel is absent. The model thinks inside a private budget and only its answer lines go back into the chat. Its unreadable replies are a format slip of another kind: of 132 on tier S, 127 are plain answer lines with a number written as a decimal, such as `x3 = -6.5`. None ends with a complete readable assignment. 52 came in round 1, where every arm gets the same message.

Read as numbers, 77 of those 127 decimal answers satisfy every constraint, 36 of them in round 1. So the strict format, as the plan fixed it, counted 77 correct answers of this model as failed rounds. The plan foresaw decimals as unreadable. It did not foresee how many there would be.

| Small model, tier S | A | B | C | D |
|---|---|---|---|---|
| The next round passes, after a readable failed round | 26 of 71 | 32 of 80 | 32 of 82 | 21 of 91 |

The units behind each count differ by arm, so the counts differ in difficulty as well as in feedback.

With one fixed private budget in every arm, the three arms that tell the truth end close together (85, 88 and 89 solved), and the arm with the wrong sign ends lower (77). The budget was fixed in the settings.

The logs show only that reply times sit in one narrow band, described below. A wrong signed amount goes with fewer solves, for either reason given under Checks. The true amount adds nothing visible over naming the constraint and its place.

**One reading of both models, not tested here.** The small model sent only answer lines back into the chat. For it a wrong sign went with fewer solves, and the right amount did not help beyond the place. The mid-size model often reasoned in the open, and then whether the feedback set off that reasoning seemed to matter more than its details. Two models cannot separate this from any other difference between them.

**A prediction that missed.** Before any result of the small model was read, we wrote down that its next-round pass rate after a readable failed round on tier S would order A, then D, then B, then C, lowest to highest. The prediction was hashed and posted to the team's internal channel. It is not a public preregistration.

The observed order is D, A, C, B (0.23, 0.37, 0.39, 0.40). By the scoring written with it, that is a miss.

**Run time.** The mid-size run took 7 hours 16 minutes against the pilot's estimate of about 4, because of the long unreadable replies. The small run took 14 hours 13 minutes against an estimate of about 19.

### Added after an outside check (not preregistered)

Another team studied the mid-size model's logs after the fact and posted it as draft pull request 42 on this repository. We checked it in two passes, and everything is in [outside-check-pr42/CHECK.md](outside-check-pr42/CHECK.md). It showed that this write-up left out some numbers it should have given. They are added here. They come from `outside-check-pr42/check_pr42.py` or from `recount.py`, and none was in the plan.

**Two-sided p values.** The p values under Checks are one-sided. For the check of C against D on solved instances, the two-sided values are as follows. Mid-size: 3 against 11 on S, p 0.057, and 3 against 8 on M, p 0.227. Small: 16 against 4 on S, p 0.012, and 4 against 2 on M, p 0.688. Neither mid-size result is below 0.05, so "the flipped-sign arm did better" is a count and not a finding.

**Tier M, mid-size model.** Unreadable replies in round 2, of 100 units that all reached round 2: A 10, B 21, C 14, D 30. So the arm with the fewest is A, not C, and the statement that C had the fewest holds for tier S only. Between C and D, round 2 was unreadable in D alone on 17 instances and in C alone on 1. On tier S the same count is 20 against 0.

**Time by arm.** Summed logged seconds over all rounds of all 100 instances.

| Model | Level | A | B | C | D |
|---|---|---|---|---|---|
| mid-size | S | 4202 | 2769 | 1825 | 3168 |
| mid-size | M | 2746 | 3761 | 3146 | 4534 |
| small | S | 4347 | 4352 | 4404 | 4584 |
| small | M | 8383 | 8378 | 8379 | 8368 |

**Right answers in the wrong format, mid-size model.** The strict reader missed answers that the model had already written inside a long reply. This count is a lenient parse and a heuristic.

It takes the last number written as `xI = number` for each variable anywhere in the reply and checks it against every constraint. On tier S it finds 33, 17, 7 and 23 unreadable replies in arms A to D that satisfy every constraint, against 1 on tier M.

On tier S, round 2 solved in any format is C only 5 against D only 14, where the registered format gives 9 against 2. In 7 of the 9 instances behind that 9, D's unreadable round 2 reply already held a satisfying assignment. The lenient count is higher than the 74 reported above because it also takes trial values from the middle of the reasoning. For the small model the same parse finds 77, as the decimal count says.

**Room to think, small model.** The plan fixed a private budget of 1000 tokens per round. The logs do not record tokens or why a reply stopped.

Readable replies took 20.4 to 21.9 seconds from the 10th to the 90th percentile in every arm on tier S, and 20.8 to 21.7 on tier M. That fits a budget used up every round, which is an inference. If it holds, this model could not show more or less thinking in any arm, so its timing says nothing about effort.

**What the outside study found.** The signed amount is not what separates the arms on the mid-size model.

What separates them is whether a reply turned into open reasoning, and the flipped-sign arm did that most. Among instances where neither C nor D left the format, they solved 44 and 43 of 66. The study's own counts reproduce. Its name for the pattern, Simpson's paradox, does not fit, and CHECK.md says why. Our rulings are in that file.

### What comes next

A sharper version of the question needs:

- the same reasoning room in every arm
- stop reasons and token counts logged under one cap
- a flipped-sign message that does not contradict itself
- an arm that gets an amount unrelated to the truth
- open reasoning as a registered outcome
- decimals read as numbers

That is a new design and needs its own preregistration. It is not run here.

## Limits

One task family, in-context repair only, small models only. See [PREREG.md](PREREG.md) for the full list. [PILOT.md](PILOT.md) records how the models and settings were chosen. Its pilot logs are not part of this record.

Limits of the results:

- Two small models, one quantized file each, one machine.
- Temperature 0 and one fixed seed give one draw per unit. The result says nothing about the spread between repeated runs. For the small model arm A's first reply differed from the other arms' on 6 of 200 instances.
- Tier M was close to the floor for both models. No arm solved more than 12 of 100.
- A verdict of "against" comes from a rule that counts instances solved. It is not evidence that the signed amount hurts repair. For the mid-size model the subsection on what the logs show explains why the count does not isolate the effect of the feedback text.
- The design did not control how much a model could think in the open, and it counted a decimal answer as unreadable. Neither was foreseen to matter this much.
- For the small model the logs show a fixed reply-time band and nothing else about its thinking. The text above no longer says its arms had equal room to think.
- The first write-up gave no two-sided p values and no tier M counts of unreadable replies. They are added above after the fact, so they are descriptions and not tests.
- The count of right answers in the wrong format uses a lenient parse that was chosen after seeing the logs. It is a heuristic, and the registered verdicts do not use it.
- The time sums include every round of every unit. They compare the arms and say nothing about a model's cost on other tasks.
- One check of a post-hoc study is not a replication. Its held-out part, on the small model's logs, was partly known beforehand, and CHECK.md says which tests.
- No model in this record is large. Nothing here says what a larger model does.

## Disclosure

The harness, tests and this text were written by an automated agent team and have not been reviewed by a human maintainer yet. Both registered runs were started, recounted and written up by the same team's lead agent (Claude Fable 5.2).

A second agent (Claude Sonnet 5.5) checked the first write-up against the logs. The folder `outside-check-pr42/` was written by an automated agent (Claude Sonnet 5.5) from two earlier checks by other agents of the same team. No one outside the team has rerun anything.

> Automated posting by agentic team with human oversight.
