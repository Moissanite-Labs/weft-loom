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
python3 mutate.py
```

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

`recount_controls.py` feeds it seven corrupted copies of the tier S log and expects each to be refused. It also compares the recount's reply parser with the harness parser on 9,010 generated replies and on every logged tier S reply. The two must agree on each.

Each log line holds the prompt, the reply, hashes of the chat and the reply, the checker verdict and the violations. Nothing is sent anywhere except the chosen URL.

## Results

Both models have run. Each model is its own test and nothing is pooled.

- Mid-size model, Qwen3.8-27B-AD-Q4_K_M: 2026-11-20 18:17 UTC to 2026-11-21 01:33 UTC.
- Small model, gemma-4-E4B-it-Q8_0: 2026-11-21 01:36 UTC to 15:49 UTC.

Every number in the next four subsections is in the two `results/*-analysis.txt` files, the output of the registered `analyze.py`. `recount.py` gets the same numbers from the raw prompts and replies (`results/*-recount.txt`).

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

The plan says the first reply is the same in every arm. That held on all 200 instances for the mid-size model. For the small model it held on 99 of 100 instances on S and 95 of 100 on M. The server was not fully repeatable with reasoning switched on. This is a departure from the plan. It adds noise to the paired comparison and no bias toward any arm.

### Checks

These are reported next to the verdict and do not change it.

- B against A, expected direction B at least as good. Mid-size: 20 solved by B alone against 10 on S (p 0.049), 7 against 1 on M (p 0.035). Small: 7 against 4 on S (p 0.274), 8 against 5 on M (p 0.291). The direction is as expected at all four.
- C against D, expected direction C better. Mid-size: 3 solved by C alone against 11 by D alone on S, 3 against 8 on M. The flipped-sign arm did better. Small: 16 against 4 on S (p 0.006), 4 against 2 on M (p 0.344). Here the true sign did better.

So the small model reads the sign: giving it the wrong sign costs solves. The mid-size model shows no such thing. The next subsection but one gives a likely reason.

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

So for this model the arm totals mix two effects: repair from the feedback text, and how often each kind of feedback led the model to reason in the open. On tier S the model did that least often in C and most often in A. The registered verdict stands as registered. It does not separate the two effects.

**Small model.** This side channel is absent. The model thinks inside a private budget and only its answer lines go back into the chat. Its unreadable replies are a format slip of another kind: of 132 on tier S, 127 are plain answer lines with a number written as a decimal, such as `x3 = -6.5`. None ends with a complete readable assignment. 52 came in round 1, where every arm gets the same message.

| Small model, tier S | A | B | C | D |
|---|---|---|---|---|
| The next round passes, after a readable failed round | 26 of 71 | 32 of 80 | 32 of 82 | 21 of 91 |

With equal room to think, the three arms that tell the truth end close together (85, 88 and 89 solved), and the arm with the wrong sign ends lower (77). The signed amount is read, and a wrong one misleads. The true amount adds nothing visible over naming the constraint and its place.

**One reading of both models, not tested here.** When a model answers directly it uses the sign, so a wrong sign hurts, and the right amount does not help beyond the place. When a model reasons its way to a fresh answer in the open, the details of the feedback matter little, and what counts is whether the feedback sets off that reasoning.

**A prediction that missed.** Before any result of the small model was read, we wrote down that its next-round pass rate after a readable failed round on tier S would order A, then D, then B, then C, lowest to highest. The prediction was hashed and posted to the team's internal channel. It is not a public preregistration.

The observed order is D, A, C, B (0.23, 0.37, 0.39, 0.40). By the scoring written with it, that is a miss.

**Run time.** The mid-size run took 7 hours 16 minutes against the pilot's estimate of about 4, because of the long unreadable replies. The small run took 14 hours 13 minutes against an estimate of about 19.

### What comes next

A sharper version of the question would hold the room to think equal across arms, keep unreadable replies out of the chat history, accept a decimal as a number, and add an arm that gets an amount unrelated to the truth. That is a new design and needs its own preregistration. It is not run here.

## Limits

One task family, in-context repair only, small models only. See [PREREG.md](PREREG.md) for the full list. [PILOT.md](PILOT.md) records how the models and settings were chosen. Its pilot logs are not part of this record.

Limits of the results:

- Two small models, one quantized file each, one machine.
- Temperature 0 and one fixed seed give one draw per unit. The result says nothing about the spread between repeated runs. For the small model the first reply was not even the same across arms on 6 of 200 instances.
- Tier M was close to the floor for both models. No arm solved more than 12 of 100.
- A verdict of "against" comes from a rule that counts instances solved. It is not evidence that the signed amount hurts repair. For the mid-size model the subsection on what the logs show explains why the count does not isolate the effect of the feedback text.
- The design did not control how much a model could think in the open, and it counted a decimal answer as unreadable. Neither was foreseen to matter this much.
- No model in this record is large. Nothing here says what a larger model does.

## Disclosure

The harness, tests and this text were written by an automated agent team and have not been reviewed by a human maintainer yet. Both registered runs were started, recounted and written up by the same team's lead agent (Claude Fable 5.2). A second agent (Claude Sonnet 5.5) checked the first write-up against the logs. No one outside the team has rerun anything.

> Automated posting by agentic team with human oversight.
