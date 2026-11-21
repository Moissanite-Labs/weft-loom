# Pilot: choosing models and settings

Date: 2026-11-20. The pilot used seeds 900000 to 900005 (tier S) and 910000 to 910005 (tier M). None of the registered seeds were run. The pilot outcomes only choose the settings below. They are not part of the result.

## What was run

Each pilot ran arm C only, with k = 2, on 6 instances, so at most 12 requests. The server ran on one slot with all layers on the GPU and a context of 8192. Temperature 0 and seed 0 come from the runner.

Server command (the model file name changes per setting):

```
llama-server -m MODELFILE --host 127.0.0.1 --port 8091 -np 1 -ngl 99 -c 8192 FLAGS
```

Runner command (MODEL is the label sent to the server, TIER is S or M, SEED is 900000 or 910000, N is the token cap):

```
python3 -B runner.py --url http://127.0.0.1:8091/v1 --model MODEL --arms C --tier TIER --base-seed SEED --count 6 --k 2 --max-tokens N --log LOGFILE
```

"Readable" counts replies that the strict parser accepts. "Round 2 solves" is out of the units still unsolved after round 1. Median tokens come from a separate pass over the six first-round prompts with the same settings. The pilot logs are not part of this record.

## Results

| Setting | Tier | Readable round 1 | Round 1 solves | Round 2 solves | Median seconds | Median tokens | Usable |
|---|---|---|---|---|---|---|---|
| Llama-3-8B Q4_0, no flags, max 512 | S | 0 of 6 | 0 | 0 of 6 | 1.0 | not measured | no |
| gemma-4-E4B Q8_0, `--reasoning off`, max 1024 | S | 6 of 6 | 0 | 1 of 6 | 1.0 | about 24 | no, no round 1 solve |
| gemma-4-E4B Q8_0, `--reasoning on --reasoning-budget 1000`, max 1400 | S | 6 of 6 | 1 | 1 of 5 | 28.2 | 1030 | yes, at the edge |
| same | M | 6 of 6 | 0 | 1 of 6 | 21.5 | 1050 | not required |
| gemma-4-26B-A4B Q4_K_M, `--reasoning off`, max 1024 | S | 6 of 6 | 3 | 1 of 3 | 0.7 | 27 | yes |
| same, max 1024 | M | 0 of 6 | 0 | 5 of 6 | 10.2 | 1024 | no |
| same, max 3072 | M | 0 of 6 | 0 | 6 of 6 | 14.2 | not measured | no |
| gemma-4-26B-A4B Q4_K_M, `--reasoning on --reasoning-budget 1000`, max 1400 | M | 4 of 6 | 1 | 0 of 5 | 20.2 | not measured | no |
| same, max 2500 | M | 4 of 6 | 1 | 1 of 5 | 21.6 | not measured | no |
| Qwen3.8-27B-AD Q4_K_M, `--reasoning off`, max 1024 | S | 6 of 6 | 3 | 1 of 3 | 3.8 | 28 | yes |
| same | M | 6 of 6 | 0 | 0 of 6 | 6.6 | 46.5 | yes, hard but readable |

Six instances is a very small sample. A rate of 1 of 6 can be a true rate anywhere from a few percent to about 50 percent. The table only shows that a setting is alive, not where its true rate sits.

## What did not work

- Llama-3-8B (Q4_0) opens every first reply with a sentence such as "Here are the rational numbers". The prompt says "and nothing else", and parsing is strict, so no first reply is readable. After the feedback message it drops the sentence and answers in format, but none of its answers solved. The Q2_K file was not tried.
- gemma-4-E4B with reasoning off answers in format in about one second, but solved none of six on tier S in round 1. That sits below the 1 of 6 floor of the usability rule.
- gemma-4-E4B with reasoning left fully on spent more than 2048 tokens on a single instance and still had an empty answer. A cap high enough to finish would take far over a minute per request.
- gemma-4-26B-A4B with reasoning off works on tier S. On tier M it writes its working in the visible reply, and even 3072 tokens did not produce a readable first reply. With a thinking budget of 1000 it still leaks working into the reply on a third of tier M instances, at either cap. So it is a good tier S model and not a usable tier M model.
- A decimal such as 2.5 is not accepted by the strict parser. gemma-4-E4B wrote one in two of its second-round replies. This is a real property of the model and is reported as unreadable, as the preregistration says.
- Qwen3.6-35B-A3B and the other large files were not tried. Two models already met the usability rule.

## Chosen settings

Small model: gemma-4-E4B-it-Q8_0, `--reasoning on --reasoning-budget 1000`, `--max-tokens 1400`. The server stops its reasoning at 1000 tokens and then prints the answer lines. The runner reads only the final answer text, as before. Every request used about 1030 to 1050 tokens, so the budget is always spent and the answer is a forced stop of the reasoning, not a finished thought. Tier S is at the edge of the rule with 1 first-round solve in 6.

Mid-size model: Qwen3.8-27B-AD-Q4_K_M, `--reasoning off`, `--max-tokens 1024`. Replies are short, always readable, and tier S gives 3 of 6 in round 1. Tier M is hard (0 of 6 in two rounds) but readable, so M can still separate the arms through rounds 3 and 4.

gemma-4-26B-A4B with `--reasoning off` is a second mid-size option for tier S only. It is not chosen because the registered run uses one setting for both tiers.

Nothing was changed in the runner, the generator, the checker, the feedback texts, the prompt, k, the tier sizes or the seeds. The server flags did all the work, so the test suite was not rerun for a code change.

## Time for the full registered run

The full run is 2 tiers, 100 instances, 4 arms, up to 4 rounds, stopping early on a solve. The estimate uses the pilot medians and a guess at the mean rounds per unit (the pilot used k = 2, so the guess is rough).

| Model | Guessed mean rounds S and M | Requests | Seconds per request S and M | Expected hours | Worst case hours |
|---|---|---|---|---|---|
| gemma-4-E4B-it-Q8_0 | 3.3 and 3.8 | about 2800 | 28 and 22 | about 19 | about 25 |
| Qwen3.8-27B-AD-Q4_K_M | 2.4 and 3.8 | about 2500 | 4 and 7 | about 4 | about 5 |

The worst case is 3200 requests at the slower per-request time. Later rounds carry longer chats, so real times will be somewhat higher.

## Proposed reduction for the small model (not applied)

The small model needs about 19 hours, which is over the 10 hour limit. The smallest reduction that fits is 50 instances per tier, with the same seeds starting at 100000 and 200000 and nothing else changed. That brings the expected time to about 9.5 hours, and the worst case to about 12.5 hours.

What it does to power, in plain terms. The test only counts instances that C solves and B does not, and the reverse. With 100 instances, a model that differs between the two arms on 10 percent of instances gives about 10 such pairs, just enough to pass the rule that asks for at least 10. With 50 instances the same model gives about 5 pairs, so the level would be reported as unable to test the claim.

To reach 10 pairs at 50 instances, the arms would have to differ on 20 percent of instances. With exactly 10 pairs, the sign test needs 9 of 10 in favour of C to reach the 0.025 threshold.

So halving the instances roughly halves the pairs and makes a "supports" result possible only if the effect is large. A fixed 100 per tier is better if time allows. The mid-size model does not need a reduction.

This change is a proposal only. It needs a dated amendment before any run.
