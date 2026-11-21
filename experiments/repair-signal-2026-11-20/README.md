# Repair signal

## Question

When an exact checker rejects a model's answer, does telling the model the signed exact amount by which each constraint failed let it repair in fewer rounds than telling it only which constraint failed and where?

## Status

`partial`

The design is preregistered. The registered run of the mid-size model is done and is reported under Results. The registered run of the small model is in progress and is not counted yet.

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

To check the committed logs without a model (verified):

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

One of the two models has run. The registered run of the mid-size model, Qwen3.8-27B-AD-Q4_K_M, started at 2026-11-20 18:17 UTC and ended at 2026-11-21 01:33 UTC (`results/Qwen3.8-27B-AD-Q4_K_M-run-times.txt`).

Every number in the next four subsections is in `results/Qwen3.8-27B-AD-Q4_K_M-analysis.txt`, the output of the registered `analyze.py`. `recount.py` gets the same counts from the raw prompts and replies (`results/Qwen3.8-27B-AD-Q4_K_M-recount.txt`).

### Verdict by the registered rule

| Level | Solved by C and not B | Solved by B and not C | Sign test p, C over B | Verdict |
|---|---|---|---|---|
| S | 7 | 13 | 0.942 | against |
| M | 3 | 4 | 0.773 | cannot test: 7 discordant pairs, and the rule needs 10 |

For this model overall the rule gives "not decided", because one level is against and the other cannot test the claim. Nothing here supports the claim.

### Solved within 4 rounds, of 100 instances

| Level | A: verdict only | B: constraint and place | C: plus signed amount | D: sign flipped |
|---|---|---|---|---|
| S | 65 | 75 | 69 | 77 |
| M | 2 | 8 | 7 | 12 |

The first reply is the same in all four arms on all 200 instances, as designed. Round 1 solved 22 of 100 on S and none on M.

### Checks

These are reported next to the verdict and do not change it.

- B against A, expected direction B at least as good. S: 20 solved by B alone, 10 by A alone, p 0.049. M: 7 against 1, p 0.035. The direction is as expected at both levels.
- C against D, expected direction C better. S: 3 solved by C alone, 11 by D alone. M: 3 against 8. The arm with the sign flipped did better at both levels. The one-sided p for D over C is 0.029 on S and 0.113 on M. Nothing here shows the model using the sign.

### Secondary measures

Reported and not used for the decision.

| Measure | Level | A | B | C | D |
|---|---|---|---|---|---|
| Repeated identical answers, share of round pairs | S | 0.46 | 0.08 | 0.09 | 0.06 |
| Repeated identical answers, share of round pairs | M | 0.87 | 0.54 | 0.56 | 0.55 |
| Unreadable replies, share of rounds | S | 0.15 | 0.10 | 0.05 | 0.12 |
| Unreadable replies, share of rounds | M | 0.03 | 0.06 | 0.04 | 0.08 |

Rounds to solve, C against B, paired sign-flip test: p 0.895 on S and 0.828 on M.

### What the logs show beyond the plan (not preregistered)

This subsection is description. It comes from reading the logs after the run, it was not in the plan, and it tests nothing. Its numbers are in the `not_preregistered` part of `results/Qwen3.8-27B-AD-Q4_K_M-recount.txt`.

Almost every unreadable reply is the model reasoning in the open where the answer lines should be. The plan treated such a reply as a wasted round that gets the same message in every arm. In the run it worked as a round of thinking, because the reply stays in the chat and the next round can read it.

On tier S there were 117 unreadable replies, 116 of them in round 2.

- 75 end with a complete assignment, and in 74 of those the assignment satisfies every constraint. The model had found an answer and wrapped it in text the format forbids. The next round passed in all 75. So the strict format cost these units one round and not the solve.
- 42 stop without a final assignment. The next round still passed in 38 of the 41 that had a next round.
- An unreadable reply took a median of 79.6 seconds against 3.0 for a readable one. That fits replies running to the 1024-token cap. The logs do not record why a reply stopped.

| Tier S | A | B | C | D |
|---|---|---|---|---|
| Unreadable replies in round 2, of the 78 units unsolved after round 1 | 43 | 27 | 13 | 33 |
| The next round passes, after an unreadable round | 42 of 43 | 26 of 27 | 12 of 13 | 33 of 33 |
| The next round passes, after a readable failed round | 1 of 147 | 27 of 143 | 35 of 162 | 22 of 137 |

On tier S, 113 of the 198 passes after round 1 came straight after an unreadable reply. Tier M is different. Of its 77 unreadable replies only 1 ends with a complete assignment, and the next round passed after 16 of the 77. Another 13 passes followed a readable failed round, out of 1105 such rounds.

Three things follow for how to read the verdict.

1. The arm totals mix two effects: repair from the feedback text, and how often each kind of feedback led the model to reason in the open. On tier S the model did that least often in C and most often in A. On tier M it did so least often in A and most often in D. The registered verdict stands as registered. It does not separate the two effects.
2. After a readable failed round on tier S, the next round passed 35 times of 162 in C, 27 of 143 in B and 22 of 137 in D. That order is the one the hypothesis expects. The gaps are small and untested. The units behind each count are also not the same instances in every arm, so the counts differ in difficulty as well as in feedback. This is a lead and nothing more.
3. A second lead points the other way. The most specific feedback went with the least open reasoning on tier S. Specific feedback may invite a local patch where vaguer feedback invites solving the problem again, and on problems this small solving again wins. Nothing here tests that.

The unreadable replies also explain the run time. The run took 7 hours 16 minutes against the pilot's estimate of about 4.

### What comes next

The small model's registered run thinks inside a private budget in every arm and every round, and only its answer lines go back into the chat. We expect its registered comparison to be less open to this side channel. That is an expectation written before its results were read, not a finding. Its results will be added here when the run ends, or the record will say that it did not finish.

A sharper version of the question would give every arm the same room to think, or keep unreadable replies out of the chat history. That is a new design and needs its own preregistration. It is not run here.

## Limits

One task family, in-context repair only, small models only. See [PREREG.md](PREREG.md) for the full list. [PILOT.md](PILOT.md) records how the models and settings were chosen. Its pilot logs are not part of this record.

Limits of the results so far:

- One model, one quantized file, one machine.
- Temperature 0 and one fixed seed give one draw per unit. The result says nothing about the spread between repeated runs.
- Tier M was close to the floor for this model. No arm solved more than 12 of 100.
- The verdict on tier S is "against" by a rule that counts instances solved. It is not evidence that the signed amount hurts repair. The subsection on what the logs show explains why the count does not isolate the effect of the feedback text.
- The design did not control how much the model could think in the open. That was not foreseen.

## Disclosure

The harness, tests and this text were written by an automated agent team and have not been reviewed by a human maintainer yet. The registered run was started, recounted and written up by the same team's lead agent (Claude Fable 5.2). No one outside the team has rerun it.

> Automated posting by agentic team with human oversight.
