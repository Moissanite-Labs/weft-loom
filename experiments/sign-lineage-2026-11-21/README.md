# Sign lineage test: its exact chance law, when it is valid, and how a copy evades it

## Question

A public site tests whether two language models share an origin by pairing up the units of their MLP layers (the feed-forward part of each block) and counting how often a pair's activations rise and fall together. What is the exact chance law of that count, when is the test valid, can a copy of a model evade it, and what does it say about small open models read on our own text?

We derived the law with proofs and exact checks, had a separate session try to refute it, and rebuilt the test on 14 small open models with a text of our own (traces from 12 of them, weights only from 2).

The count has an exact chance law whenever either model's units have free signs, a binomial or a related cluster law, and two exact checks tell whether they do. The site's own numbers come out close where we could rebuild them. A copy with its units reordered and their signs flipped at random passes as unrelated.

## Status

`exploratory`

The real-model part followed a plan that was written and hashed before any model was loaded. That hash was recorded on one machine only, and the plan first appears in git together with its results, so this record makes no public preregistration claim.

The derivation rests on proofs with exact checks. A second checker with its own code recomputed the real-model numbers. Every analysis that was not in the plan is marked post hoc.

## What this is

The site [qwen-neuron-map.pages.dev](https://qwen-neuron-map.pages.dev) maps the MLP units of about 30 language models. An MLP layer is the part of each transformer block that widens the signal into many hidden units, applies a fixed curve, and narrows it back. A unit's activation on a stretch of text is the list of values it takes, one per word. We call that list its trace.

The site's lineage test matches each unit of one model to the unit of the other model whose trace is most similar, and counts how often the pair moves together (their correlation is positive) rather than in opposite directions. The site says unrelated models move together about half the time, like a coin, and models that share an origin nearly always.

This record works out the exact chance law of that count, states when the test is valid and gives two exact checks for it, shows how a copy can evade it, and rebuilds the test on small open models with a text of our own.

The site published no code, no text it read, and no license. The main study here uses none of the site's data. The site's sentences that we test are quoted in [site_claims.json](site_claims.json) and taken on trust. Every model number below is our own measurement.

The separate outside check in [outside-check-audit059/](outside-check-audit059/) reads the site's public pages to check another team's counts, and those pages are not included.

## Findings

Each finding says what kind of evidence it rests on. The proofs are written out in [derivation/STATEMENTS.txt](derivation/STATEMENTS.txt) (S1 to S6), and the refuter's report and rulings in [derivation/refute/REFUTE.txt](derivation/refute/REFUTE.txt) and [REFUTE-RULINGS.json](derivation/refute/REFUTE-RULINGS.json). Where the refuter tightened a statement, the findings below give the tightened form.

**What reproduces.** Where we could rebuild the site's numbers, they come out close, in one case only under a post hoc reading. Here a strong pair is a matched pair whose correlation is at least 0.3 in size, the plan's main cut.

- Unrelated models agree about half the time, as the site says. When either model has free signs this is a theorem (finding a).
- The site's caveat, quoted in finding c, names two models, Pythia, whose units cannot point either way, and Falcon-H1 Tiny, whose units lean to one side, and puts their agreement at 83 to 87 percent. We measure 0.868 of strong pairs (finding c).
- The site's coin rule holds on a known pair: SmolLM2-135M and its Instruct fine-tune agree in nearly every strong pair, with nearly every unit in the same position. SmolLM2-135M and 360M, which the site counts as unrelated, sit at chance (finding d).
- The two Qwen3.5 models we read agree in 0.869 of strong pairs, against the site's 93 percent (finding d).
- The site's numbers for Pythia's training checkpoints come out close when units are matched within each layer, a post hoc reading (finding f).

The findings then narrow when the test is valid and how a copy evades it.

**a. Why about half.** *Proof with an exact check.*

In a gated MLP block the output is down applied to act(gate x) times (up x). Here x is the block's input, gate, up and down are weight matrices, act is a fixed curve such as SiLU, and the product is taken unit by unit. SmolLM2, Qwen3.5, Gemma 4, Falcon-H1 and many other models use this form ([anchors.json](anchors.json)).

Each hidden unit owns one row of gate, one row of up and one column of down. Flip the signs of its up row and its down column, and the model computes exactly the same function while that unit's trace changes sign. So as far as the function goes, the sign of every unit is a free choice. We call this the unit's sign symmetry. It is a property of the block's form.

Common optimisers keep that symmetry. Plain gradient descent, momentum, Adam, AdamW, weight decay and clipping by the total gradient size all treat a flipped model exactly as they treat the original.

A second implementation trained a small randomly initialised model built from the Qwen3 code in transformers, with 14 torch optimiser settings, and found the flipped and original runs bit for bit equal after 60 steps, while a loss term that prefers one sign broke the equality.

So a model with the sign symmetry, trained on its own from random starting weights that are as likely negative as positive, ends with each unit's sign set by a fair coin. We say such a model has free signs. Free signs are a property of the trained weights, and a model can have the symmetry without them.

The coin is lost when something in training ties a unit's sign. The derivation and the refuter list these cases:

- A plain block whose curve is not odd (finding b).
- A loss term or a quantiser that prefers one sign of a unit, such as a penalty on a unit's mean or a quantiser with an off-centre zero point.
- Starting weights that are not symmetric, or that come from another model. The second is the lineage the test looks for.
- Distillation that matches the student's unit activations to a teacher's. Distillation on outputs alone does not tie signs.
- A LayerNorm applied to the hidden vector, which subtracts the mean. An RMSNorm there keeps the symmetry.
- Two runs started from the same seed, which share every coin.
- Float rounding of the starting-weight law, which makes it symmetric only up to the last bit. The bias on each unit's coin is of order the input width times 2^-24, which is negligible.

Call the model whose every unit is matched once the source, and the other the target. Call m the number of matched pairs and N+ the number that move together.

If the source has free signs and does not depend on the target, N+ is exactly Binomial(m, 1/2), the number of heads in m fair coin tosses, whatever the matching. Each source unit sits in exactly one pair, so its coin moves only that pair.

If only the target has free signs, several source units can share one target unit, and their pairs flip together on that unit's coin. For each target unit, take its matched pairs that move together minus those that do not, and call that its cluster total.

Then twice N+ equals m plus the sum, over target units, of each cluster total with a random sign: N+ = (m + Σ_j e_j |s_j|)/2, where s_j is target unit j's cluster total and the e_j are independent fair signs. We compute this law exactly by whole-number convolution. We call it the cluster law.

An independent refuter tightened three points, and they hold here. The cluster law equals the binomial only when every target unit is matched at most once: three pairs on one target with signs plus, plus, minus have a total of one but a different law. A pair whose correlation is exactly zero has no sign and must be dropped. Ties in the matching must be broken at random, not by unit order.

Brute-force enumeration of every sign pattern agrees with the cluster law in 397 of 397 small cases and with the binomial in 300 of 300, in code that shares nothing with ours.

**b. When the test is not valid, and two exact checks anyone can run.** *Exact under the stated null, measured on named models. Check two, the two extra Falcon downloads and the per-unit agreement are post hoc.*

The site already names the two models below as cases where the test does not apply (its caveat, quoted in finding c). What this finding adds is the reason, and checks that decide it for any model.

A plain block, output = down applied to act(up x), has no sign symmetry unless act simply changes sign when its input does, as tanh does and GELU does not. Pythia uses this form with GELU, whose output has a long positive tail and a small negative floor. So its traces are lopsided in the same direction in every model, and unrelated models agree far above half.

Three pairs of separately trained Pythia-160m seeds agree in 21312 of 21539, 21469 of 21683 and 21392 of 21617 strong pairs, 0.989 to 0.990.

A gated model has the symmetry but can still lack free signs. In Falcon-H1-Tiny-R-0.6B the gate row and the up row of a unit point the same way, meaning their inner product is positive, in 70500 of 90112 units. A free sign gives one half. The same count, 70500 of 90112, holds in its version from before the reinforcement-learning stage, a different file, and the family's 90M base model gives 12162 of 18432.

Check one, from activations: count the units whose trace has positive skew, a longer tail on the positive side. Check two, from weights alone with no text needed: count the units whose gate row and up row have a positive inner product. Under free signs both counts are exactly Binomial(units, 1/2), because a flip reverses both.

A model that fails either check cannot serve as the free-sign side of the laws in finding a.

SmolLM2 and Qwen3.5 pass both checks, with two-sided p-values from 0.18 to 0.87. All six Pythia models fail check one, with at least 36802 of 36864 units of positive skew. Falcon fails both. The counts for every model are in the second results table.

The cause of Falcon's lean is not identified. Per unit, the weight check predicts the sign of the skew in 71435 of 90112 units, so the alignment is a strong partial account and not a complete one. The lean is already present before the reinforcement-learning stage. Whether it comes from the starting weights, pretraining or supervised fine-tuning is not known.

**c. The site's own caveat, reproduced, with a post hoc reading.** *Measured on named models and one text, with exact p-values. The pairs against SmolLM2-135M are post hoc.*

The site says Pythia's units cannot point either way and Falcon-H1 Tiny's lean to one side, so those two agree 83 to 87 percent of the time without being related. We measure 12083 of 13925 strong pairs from Pythia-160m to Falcon-H1 Tiny moving together, 0.868. With every pair kept it is 31053 of 36864, 0.842.

One leaning side is not enough. Against SmolLM2-135M, whose signs are free, Pythia's share falls to 8964 of 16697 (0.537) and Falcon's to 5511 of 10474 (0.526). Both lie inside the 99.9 percent cluster-law band, with two-sided p 0.11 and 0.014.

The plain binomial would wrongly reject the Pythia pair at p 1.7e-21, because many Pythia units share one SmolLM2 unit. The cluster law gives 0.11. So in these data the high share appears only when both models lean. This shows the share returns to chance with one free partner. It does not prove that both sides must lean in every case.

**d. The test on real models.** *Measured on named models and one text, with exact p-values.*

SmolLM2-135M and its Instruct fine-tune, whose model card names 135M as its base: 46068 of 46078 strong pairs move together, exact one-sided p 1.6e-13831. 46059 of 46080 units are matched to the unit with the same layer and index, where chance expects about 30.

SmolLM2-135M and SmolLM2-360M, two sizes trained separately: 7900 of 15958, two-sided p 0.21, inside the chance band.

Qwen3.5-0.8B and Qwen3.5-2B: 43460 of 49991 (0.869), one-sided p 2.0e-6636. Only 8 of 86016 units sit at the same position, against a chance mean of 8.75 (p 0.65). The site's entry for Qwen3.5-2B gives 93 percent for this pair (quoted in site_claims.json).

A rejection means the two models' unit signs are tied, so they are not independent draws with free signs. It does not say how they are tied. One model may be made from the other, both may start from a shared initial state (two runs from one random seed count), or one may have been trained to copy the other's activations.

**e. How a copy evades it.** *Measured on named models, plus a theorem. The comparison with another test is sampled on small networks.*

We built a copy of SmolLM2-135M-Instruct in which every MLP block's units are put in a random order and each unit's sign is flipped by a fair coin. It computes the same function: the largest difference in logits (the model's raw scores for the next token) over the whole text is 3.9e-4, where logits reach 51.07 in size.

Against SmolLM2-135M the copy's sign count falls to 23088 of 46078 (two-sided p 0.65), and only 20 units sit at the same position against a chance mean of about 30 (exact p 0.978). Both tests call the copy unrelated.

A statistic that ignores order and sign, the mean over source units of the largest absolute correlation, is unchanged: 0.9226 for the copy and for the true Instruct model, against 0.2917 for the unrelated 360M model and 0.0381 when the word order is shuffled. The second checker built its own copy from another seed and got the same picture: 23053 of 46078 (p 0.90), 27 at the same position (p 0.73).

The general reason is simple. The sign test's chance law comes from a symmetry of the model: flipping or reordering units changes nothing it computes. A copy hit by a random flip and a random reordering has, by construction, coin-flip signs and a random order, whatever its history.

A test whose chance law comes from a symmetry therefore cannot see a copy that was hit by a random element of that same symmetry. Such a copy can be seen only through what that symmetry leaves unchanged, or through a symmetry the copier did not randomise.

A statistic of the first kind gets no exact chance law from that symmetry. Our order-and-sign-blind statistic is of the first kind. The matching test below also uses something a per-unit sign flip leaves unchanged: the gate activations.

The complement comes from the matching test of Zhu, Ahmed, Kuditipudi and Liang (ICML 2025). It matches units of two models by the signed similarity of their gate and up activations and asks whether the two matchings agree.

On a small gated network over 60 seeds, random per-unit flips do not defeat it: about half the units still match their true partners, the median rank correlation stays at 0.507, and every seed is flagged at p below 0.01. The sign count falls to 0.504 there, which is chance.

Flipping a whole layer's units at once does defeat their test: the median rank correlation falls to -0.036 and only 0.02 of the seeds are flagged. Their own list of harmless changes includes multiplying a layer's MLP matrices by a nonzero constant, and a constant of -1 is this flip. The sign count gives 0.000 there, which a two-sided test flags.

So the two tests fail on opposite cases. Matching by absolute similarity repairs theirs: it keeps a rank correlation of 1.000 in every case above. This toy result is sampled on a small synthetic network and has not been run on a real model.

**f. Two sentences of the site checked against the law.** *Exact under the stated null, and one post hoc reading.*

The site says every unrelated pair with at least 200 strong matches lands between 33 and 59 percent, over 496 compared pairs. Under the binomial, the chance that one pair with 200 to 1000 matches lands at 33 percent or lower is at most 1.5e-6, and smaller above 1000. Added over 496 pairs, a union bound that holds however the pairs depend on each other, the chance that any pair lands that low is at most 7.4e-4.

If each pair was tested in both directions, the bound doubles to 1.5e-3. Each further pair, such as those of the 6 more Gemma 3 models the site also compared, adds at most 1.5e-6.

So the binomial law, applied to the 496 pairs, is rejected at p at most 7.4e-4, or 1.5e-3 with both directions. The derivation and the refuter leave four explanations, and the site's text does not tell them apart.

- The 33 percent pair's source lacks free signs: a plain block such as Pythia, or a gated model whose coin was lost (finding a). Then the cluster law governs and the spread is wider. In our small networks with a plain GELU source and a gated target, unrelated pairs ranged from 0.355 to 0.633 at 256 matches.
- The site pools the matches of both directions, so each model's units appear more than once and the count is not of the form the laws assume.
- The site's matching or co-firing rule is not a sign-blind function of the size of the correlation.
- The two models have a real relation in which their units are anti-aligned.

The site also says that after 1,000 training steps only 18 percent of Pythia-160m's units are the unit they end as. Matching across all layers, as our plan fixed, gives 2344 of 36864 (6.4 percent). Matching only within the same layer gives 6044 of 36864 (16.4 percent), and 33672 (91.3 percent) and 36475 (98.9 percent) at steps 8,000 and 32,000, where the site says 92 and 99.1.

A seed control under the same within-layer rule stays at chance, 8 units with p between 0.89 and 0.92. We found this reading after seeing the planned result, so it is a lead about the site's unpublished rule and not a finding.

**g. Looped and expert models such as Inkling 2 Mini.** *Read from code, not run.*

Inkling 2 Mini stores 24 layers and runs layers 6 to 17 three times per token. Each layer holds 128 experts. An expert computes down applied to 4 tanh(g/4) times sigmoid(g) times 25 tanh(u/25), where g and u are the unit's gate and up values. The up branch passes through 25 tanh(u/25), which is odd: it flips sign when u does. So the expert block is gated in the sense above and has the sign symmetry.

Whether its trained signs are free is not known. By the publisher's account, its experts were trained in a 4-bit format, pruned from 384 to 128 per layer during training and then healed on distilled tokens, and we did not check whether these steps keep a fair coin. Check two on its weights would test it.

A unit in the looped layers is stored once and used on three passes. It has one coin and three traces. The three traces are one cluster, not three units, and if the looped model is the source, the binomial no longer applies and the cluster law is needed with the roles swapped.

If experts were made by copying one dense MLP layer, unit i of every copy shares one coin, and the cluster is the original unit across experts. Whether Inkling 2 Mini's experts were made that way is not stated in what we read.

## Results

All p-values are exact under the stated null, computed with whole numbers or fractions. Very small ones are shown rounded. Strong pairs have correlation at least 0.3 in size. "Same position" counts source units matched to the unit with the same layer and index, over all kept units.

### Pairs of models

| Source to target | Law that applies | Strong pairs moving together | Exact p | Same position (chance mean, p) | Order-and-sign-blind statistic |
|---|---|---|---|---|---|
| SmolLM2-135M to itself (check) | binomial | 46080 of 46080 | | 46080 of 46080 | 1.0000 |
| SmolLM2-135M to 135M-Instruct | binomial | 46068 of 46078 | one-sided 1.6e-13831 | 46059 (29.99, p at most 3.7e-126753) | 0.9226 |
| SmolLM2-135M to 360M | binomial | 7900 of 15958 | two-sided 0.214 | shapes differ | 0.2917 |
| SmolLM2-135M to reordered and flipped copy | binomial | 23088 of 46078 | two-sided 0.651 | 20 (29.99, p 0.978) | 0.9226 |
| SmolLM2-135M to the checker's copy, other seed | binomial | 23053 of 46078 | two-sided 0.900 | 27 (29.99, p 0.732) | 0.9226 |
| SmolLM2-135M to Instruct, word order shuffled (check) | binomial | none strong. All pairs: 23045 of 46080 | two-sided 0.967 | 0 | 0.0381 |
| Qwen3.5-0.8B to Qwen3.5-2B | binomial | 43460 of 49991 | one-sided 2.0e-6636 | 8 (8.75, p 0.646) | 0.3637 |
| Pythia-160m main to seed 1 | none | 21312 of 21539 | | 10 (3.82, p 0.0059) | 0.3476 |
| Pythia-160m main to seed 2 | none | 21469 of 21683 | | 2 (3.57, p 0.872) | 0.3498 |
| Pythia-160m seed 1 to seed 2 | none | 21392 of 21617 | | 4 (3.67, p 0.499) | 0.3477 |
| Pythia-160m step 1,000 to main | none | 15397 of 15637 | | 2344 (2.58, p at most 2.1e-4354) | 0.3001 |
| Pythia-160m step 8,000 to main | none | 31885 of 31897 | | 31958 (10.79) | 0.4218 |
| Pythia-160m step 32,000 to main | none | 36707 of 36711 | | 36356 (11.88) | 0.6531 |
| Pythia-160m to Falcon-H1 Tiny | none | 12083 of 13925 | | shapes differ | 0.2915 |
| Falcon-H1 Tiny to Pythia-160m | none | 6762 of 9011 | | shapes differ | |
| Pythia-160m to Falcon gate factor only | none | 17350 of 18229 | | shapes differ | 0.3173 |
| Pythia-160m to SmolLM2-135M (post hoc) | cluster | 8964 of 16697 | two-sided 0.113 (plain binomial would give 1.68e-21) | shapes differ | 0.3131 |
| Falcon-H1 Tiny to SmolLM2-135M (post hoc) | cluster | 5511 of 10474 | two-sided 0.0136 (plain binomial would give 8.99e-8) | shapes differ | 0.1928 |

Sources: `real-models/out/stats/`, `real-models/RESULTS.json`, `real-models/out/plain_binomial_contrast.txt`, and `real-models-check/out/compare.json` for the exact same-position p of the copies and for the checker's copy. The order-and-sign-blind statistic is at all pairs kept. Pooling both directions of the Pythia and Falcon pair gives 18845 of 22936.

"Falcon gate factor only" is an extra trace planned as exploratory: Falcon's act(gate x) alone, without the up branch. That factor does not flip under the symmetry, so it stands in for a site trace that is not the full product.

### The two validity checks per model

Check one counts units whose trace has positive skew. Check two counts units whose gate row and up row have a positive inner product. Under free signs both are exactly Binomial(units, 1/2). Two-sided exact p-values. Pythia's plain block has no gate, so check two does not apply to it.

| Model | Block | Check one | p | Check two | p | Free signs |
|---|---|---|---|---|---|---|
| SmolLM2-135M | gated | 23183 of 46080 | 0.184 | 22971 of 46080 | 0.523 | passes |
| SmolLM2-135M-Instruct | gated | 23091 of 46080 | 0.638 | 23060 of 46080 | 0.856 | passes |
| SmolLM2-360M | gated | 41087 of 81920 | 0.377 | 41038 of 81920 | 0.588 | passes |
| Qwen3.5-0.8B | gated | 42976 of 86016 | 0.830 | 42974 of 86016 | 0.819 | passes |
| Qwen3.5-2B | gated | 73695 of 147456 | 0.866 | 73680 of 147456 | 0.805 | passes |
| Falcon-H1-Tiny-R-0.6B | gated | 64683 of 90112 | 3.1e-3843 | 70500 of 90112 | 4.3e-6626 | fails |
| Falcon-H1-Tiny-R-0.6B before the RL stage | gated | not captured | | 70500 of 90112 | 4.3e-6626 | fails |
| Falcon-H1-Tiny-90M-Base | gated | not captured | | 12162 of 18432 | 1.4e-418 | fails |
| Pythia-160m main, seed 1, seed 2 | plain | 36802, 36817, 36833 of 36864 | each below 1e-10899 | no gate | | fails |
| Pythia-160m steps 1,000, 8,000, 32,000 | plain | 36864, 36859, 36854 of 36864 | each below 1e-10899 | no gate | | fails |

Sources: `real-models/out/models/` and `real-models/out/weights/weight_lean.json`. Check two is post hoc. Its Qwen3.5 counts were corrected here (see Preregistration, item 12).

### Small trained networks

Sampled, on two-block networks with 128 units per block (256 matched pairs) trained on a synthetic next-token task. "Flagged" means one-sided p below 0.01. Source: `derivation/RESULTS.json`.

| Arm | Pairs | Share moving together, mean (range) | Flagged by binomial | Flagged by cluster law |
|---|---|---|---|---|
| Unrelated gated networks | 200 | 0.498 (0.414 to 0.574) | 0 | 1 |
| Unrelated plain GELU networks | 100 | 0.971 (0.930 to 0.996) | 100 | 100 |
| Unrelated plain ReLU networks | 100 | 0.956 (0.906 to 0.988) | 100 | 100 |
| Unrelated plain tanh networks (symmetric curve) | 50 | 0.498 (0.438 to 0.539) | 0 | 0 |
| Plain GELU source, gated target | 100 | 0.493 (0.355 to 0.633) | 11 | 0 |
| Gated source, plain GELU target | 100 | 0.495 (0.418 to 0.578) | 1 | 1 |
| Descendant, 3000 more steps on another task | 40 | 0.858 (0.809 to 0.898) | 40 | 40 |
| Same start, other data order | 40 | 0.998 (0.988 to 1.000) | 40 | 40 |
| Copy with units reordered and flipped at random | 40 | 0.497 (0.457 to 0.559) | 0 | 0 |

The binomial over-rejects only where the source lacks free signs, as the law says.

One run with a fixed source network flagged 6 of 200 under both laws (one-sided, p below 0.01, counting every matched pair). Four replications with other fixed sources flagged 1, 2, 2 and 2 under the cluster law. With the 0.3 cut the first run flagged 8 and the replications 1, 0, 1 and 1.

We read the first as chance among the many arms and cuts we looked at, and keep it on record. Every descendant arm we ran was flagged in 40 of 40 pairs.

### Predictions

Fixed in the plan before any model was loaded, and scored by the plan's own rules as re-judged by the second checker. Source: `real-models/RESULTS.json` and `real-models-check/out/compare.json`.

| Id | Prediction | Observed | Outcome |
|---|---|---|---|
| P1 | 135M to Instruct: share at least 0.95, same position at least 0.90 | 46068 of 46078, same position 46059 of 46080 | hit |
| P2 | 135M to 360M: share inside the binomial 99.9 percent band, both pass check one | 7900 of 15958, p 0.214, checks p 0.184 and 0.377 | hit |
| P3 | All six Pythia models fail check one, seed shares at least 0.80, seed same position at chance | all fail, shares 0.989 to 0.990, same position p 0.0059, 0.872, 0.499 | hit |
| P4 | Step 1,000 same position between 0.08 and 0.35 with p below 0.001, and rising from step 1,000 to 8,000 to 32,000 | 2344 of 36864 is 0.064, below the band. It does rise. | partial |
| P5 | Falcon fails check one, Pythia to Falcon share at least 0.75 | 64683 of 90112, share 12083 of 13925 | hit |
| P6 | Reordered and flipped copy: same function, sign share and same position at chance, blind statistic "within 5 percent (relative) of its value for" Instruct and at least 0.10 above the 360M pair's | logit gap 3.9e-4, p 0.651, same position p 0.978, 0.9226 against 0.9226 and 0.2917 | hit |
| P7 | Qwen3.5-0.8B to 2B: share at least 0.85 | 43460 of 49991 | hit |
| M1 | Falcon passes check one and its pairs with Pythia sit inside the chance bands | Falcon fails check one | miss |
| M2 | Pythia seed pairs: mutual closest matches between 0.03 and 0.20 | 3089, 2988 and 3080 of 36864 | hit |
| M3 | Same position, step 8,000 between 0.60 and 0.98, step 32,000 between 0.85 and 1.00 | 31958 and 36356 of 36864 | hit |
| M4 | Pythia to Falcon gate factor alone: share at least 0.75 | 17350 of 18229 | hit |

M1 to M4 were marked in the plan as the first run's own guesses. M1 missed: Falcon's gated units lean. P4 missed its first half because the all-layer match finds few same-layer partners at step 1,000 (finding f).

The first run scored P6 as partial because its planned same-position routine returned the bracket 0 to 1, then added a bound after seeing the result. The second checker showed that the routine stopped its series too early, and the exact p is 0.978, so the plan's own rule gives a hit.

## Prior work and what is new

| Work | What it already has | Checked how |
|---|---|---|
| Zhu, Ahmed, Kuditipudi, Liang, Independence Tests for Language Models, ICML 2025 (arXiv 2502.12292) | Exact p-values from a symmetry of training, for unit reordering. A same-position test and a matching test of gate and up activations. The point that a reordered copy evades a reordering test. No sign symmetry. | Full text of arXiv v2 and the ICML version. Released code read at commit 5e65e7b, not run |
| Sweeney, Signed-Permutation Coordinate Transport for RMSNorm Transformers (arXiv 2606.31963) | The sign symmetry of gated MLP units and its absence in plain blocks. Matching by absolute similarity, then reading the sign. Version 2 adds lineage by same-index retention on the residual stream, with plus signs kept in related models and an empirical shuffled baseline near 0.497. No exact law, no MLP units, no p-value. | Full text of v1 and of v2 (HTML) |
| Kim, Same Function, Different Gradients (arXiv 2611.02052) | The per-unit up and down rescaling with the gate fixed, for positive scales only | Full text, v1 |
| Yan and co-authors, And Then There Were None (arXiv 2205.00199) | Function-preserving sign flips used to defeat white-box watermarks, in CNNs | Full text, v2 |
| Thakur and Khoury, Training Leaves Traces (arXiv 2608.14929) | A lineage score that ignores signs and order, with an empirical null and a conformal p-value | Full text, v2 |
| Li and co-authors, Transformers Are Born Biased (arXiv 2602.05927) | A lineage test from bias profiles at initialisation, with a fitted Gaussian null | Full text, v1 |
| Piven and co-authors, Permutation-Equivariant Flow Matching (arXiv 2609.32833) | Symmetric start plus equivariant training gives a symmetric law, for permutations | The relevant section of the full text, v1 |
| Canay, Romano, Shaikh, Randomization Tests Under an Approximate Symmetry Assumption, Econometrica 2017 | Exact randomization tests with sign changes over clusters | Working paper of May 2016, full text. The published version was not read |
| Li, Yosinski, Clune, Lipson, Hopcroft, Convergent Learning, ICLR 2016 (arXiv 1511.07543), and Gurnee and co-authors, Universal Neurons in GPT2 (arXiv 2401.12181) | Matching units across separately trained networks by activation correlation, including Pythia-160m seeds | Full text, v3 and v1 |
| HuRef (arXiv 2312.04828) and Witness Overlap (arXiv 2609.31784) | Lineage from weights, robust to reordering. Neither uses unit signs | Full text, v5 and v2 |

The label we defend is a concrete advance on known ground. The symmetry, matching by absolute similarity, the half-and-half rate between unrelated models, and the recipe of exact nulls from training symmetry are all known.

What is new is narrow: the exact law and p-value for sign agreement of matched units as a lineage statistic, and the conditions under which it is valid. The two exact checks are those conditions made testable, and we claim no novelty for the checks themselves.

A further observation, that the sign test and the matching test of Zhu and co-authors fail on opposite cases, is shown only on a small synthetic network. It should be confirmed on a real gated model before it is stated as a finding.

We searched by mechanism under several names and found no prior use of matched-unit sign agreement as a lineage test with an exact law. Not finding a prior use is weak evidence: searches miss work, and new preprints appear daily.

## Preregistration

Not public. The plan [real-models/PLAN.txt](real-models/PLAN.txt) with its predictions was written and hashed before any model was loaded. Its SHA-256 is `96c15d4b2cbbfc748990a03645e3b455a083e0b66e2c2059cededd5e48b9205c`. The hash was recorded locally and is not a public timestamp. The second checker found the hash matching and the file read-only, with modification times before the first download and the first trace, which can be reset and so only support the order.

The committed copy differs from the hashed file in three strings, so its own hash is `fa1ee256328fae323fe9962083437d64cb0c6504788980266bd59cdb60016c3a`. A team name on line 3 became `[name removed]`, and two local folder prefixes on line 19 became `[local clone]`.

The plan cites its sources by their working paths. Here is where each one is in this record:

- The folder `homology/real-models/` is `real-models/`.
- `../first-principles/STATEMENTS.md` is [derivation/STATEMENTS.txt](derivation/STATEMENTS.txt).
- `../first-principles/refute/REFUTE.md` is [derivation/refute/REFUTE.txt](derivation/refute/REFUTE.txt).
- The rulings in `../first-principles/REFUTE-RESULT.json` are [derivation/refute/REFUTE-RULINGS.json](derivation/refute/REFUTE-RULINGS.json).
- `../site-method/METHOD.md` is a working note on the site that is not published. The site sentences the plan relies on are quoted in [site_claims.json](site_claims.json).

Deviations declared by the first run:

1. One code chunk spans the end of `textwrap.py` and the start of `fractions.py`, joined by a blank line. The plan said each chunk is one piece of one source. It affects 1 of 100 chunks.
2. The book came from a Project Gutenberg mirror because the main site was down. The plan named that mirror in advance.
3. The same-position routine gained a lower bound after the P6 result was seen. Both scores were reported, and the second checker's exact value settles P6 as a hit.
4. p-values below 1e-300 are displayed rounded. Every decision uses the exact fraction.
5. Post hoc analyses: Pythia and Falcon against SmolLM2-135M, matching within layers, the weight check, two extra Falcon downloads, per-layer tables and a load check.
6. Light statistics jobs sometimes ran while a GPU pairing job ran. No two capture or pairing jobs overlapped.
7. Qwen3.5 checkpoints include a vision part. They were loaded as text models, and the loaded text weights equal the file.

Deviations found only by the second checker:

8. The prose keeps the Gutenberg file's Windows line ends, 812 carriage returns. This fits "original whitespace kept" but matters to anyone rebuilding the text.
9. The plan asked for the largest gap between the float32 screen and float64 over a full block of 2,048 rows. The first run reported the gap at the best match and on candidate entries only. The checker recomputed 256 full rows per pair and found a largest gap of 4.6e-5 against the 2e-3 margin (`real-models-check/out/screen_check.json`).
10. The plan's screen keeps every target within 2e-3 of the row maximum. The code keeps the top 8 per row and column and recomputes a row in full when the eighth is still inside the margin. The effect is the same.
11. The plan does not fix the cut for the blind statistic. The first report quoted the value at 0.3, while the scorer used all pairs. P6 holds at every cut.
12. The weight-check script keyed layers by number only, so in Qwen3.5 the extra prediction head overwrote decoder layer 0. The script is fixed here, and the corrected counts are 42974 of 86016 and 73680 of 147456 instead of 42954 and 73735. The conclusion, about one half, stands. After the fix all 677 numbers the checker compared agree.

Changes made for publication: the proofs and the refuter's report are kept as written apart from private names and paths, as plain text so that the line numbers the refuter cites stay fixed.

Local paths in scripts became command-line options, local paths inside output files became placeholders or source names, and the corpus builder records source names instead of paths. The derivation, the small networks and the prior-work check were not preregistered.

## How to rerun

Hardware and software of the original run: one Apple M1 Max laptop on macOS 27. Python 3.14.6 with numpy 2.5.4, scipy 1.18.1 and sympy 1.14.0 for the exact checks and the prior-work toy. Python 3.12.15 with torch 2.15.0 on the Apple MPS device, transformers 5.22.2, numpy 2.5.4, safetensors 0.8.0 and huggingface_hub 2.4.0 for models. Run from this folder in a weft-loom checkout.

Exact checks, standard library only. Each runs under `python3 -I -B`, `-I -O -B` and `-I -B -W error` and compares outputs byte for byte:

```
sh derivation/scripts/run_exact_parity.sh
bash derivation/refute/scripts/run_parity.sh
bash real-models/scripts/run_exact_parity.sh
bash real-models-check/scripts/run_exact_parity.sh
python3 -I -B real-models/scripts/plain_binomial_contrast.py
```

Small networks, torch needed. Seeds are fixed in `train_all.py`, and the refuter's runs take a master seed:

```
for e in null_h128 null_h64 null_h256 null_otherorder plain_relu plain_gelu plain_tanh descend siblings planted; do
  python -I derivation/scripts/train_all.py $e; done
python -I derivation/scripts/analyze.py && python -I derivation/scripts/invariant_holdout.py
python -I derivation/scripts/equivariance_float.py && python3 -I -B derivation/scripts/collect.py
python -I derivation/refute/scripts/sampled_refute.py 500000 out500000.json   # also 600000 and 700000
python -I derivation/refute/scripts/equivariance_refute.py
```

Real models. Downloads go to `real-models/hf/`, about 12 GB. Traces go to `real-models/traces/`, about 32 GB of float16. Neither is committed. Capture and pairing took about an hour on the machine above. `PYTHON` names an interpreter with torch and transformers.

```
python -I real-models/scripts/download.py real-models 1 2 3 5
python -I real-models/scripts/download_extra.py real-models tiiuae/Falcon-H1-Tiny-R-0.6B-pre-GRPO tiiuae/Falcon-H1-Tiny-90M-Base
python3 -I -B real-models/scripts/build_corpus.py --root real-models --gutenberg 1661-0.txt --textwrap textwrap.py \
    --fractions fractions.py --gate-contracts 09-gate-contracts.md --inertia 10-exact-inertia-certificates.md
for k in s135 s135i s360 s135L; do HF_HUB_OFFLINE=1 $PYTHON -I real-models/scripts/capture.py real-models $k; done
$PYTHON -I real-models/scripts/pairs.py real-models s135 s135i
PYTHON=$PYTHON bash real-models/scripts/run_queue.sh && PYTHON=$PYTHON bash real-models/scripts/run_queue2.sh
$PYTHON -I real-models/scripts/stats.py real-models models s135 s135i s360 s135L py py_s1 py_s2 py_1k py_8k py_32k falcon falcon_gate q08 q2
$PYTHON -I real-models/scripts/stats.py real-models pair <pair name>          # for each pair in real-models/out/stats/
$PYTHON -I real-models/scripts/within_layer.py real-models py_1k py          # also py_8k, py_32k and py_s1
$PYTHON -I real-models/scripts/weight_lean.py real-models <model folder>...  # the eight models in weight_lean.json
python3 -I -B real-models/scripts/score.py real-models
```

The corpus builder's docstring names the five source files with their SHA-256 values and stops on any mismatch. Seeds: the reordered and flipped copy uses 777, ties are broken with PCG64(20261121), the word shuffle uses 4242, and the checker's own copy uses 5150.

Second checker: `real-models-check/scripts/modelstats.py` per model, then `run_pairs.sh`, then `compare.py`, `weights_check.py`, `within_layer_mine.py`, `laund_check.py`, `hookcheck.py` and `corpus_check.py`. Each script's docstring gives its arguments, and `--real-models DIR` points at the first run's folder. Prior-work toy: `python3 -I -B prior-work-check/zhu_signflip.py`.

## Limits

- One text of 20,000 words in three kinds, prose, code and mathematical prose. No second or held-out text checks how the shares depend on the text.
- Small models only, from 135M to 2B parameters. Nothing here was run on a model above 2B.
- The exact laws are proved, but how well they hold in practice was measured only on small trained networks. On real models we only see that free-sign pairs land inside the band.
- The order-and-sign-blind statistic has no exact law. It was compared with one unrelated pair and one shuffle only, so it detects nothing in a calibrated sense here.
- The cause of Falcon's lean is unknown. The weight check accounts for 79 percent of the skew signs, not all.
- Every number of the site is taken on trust. Its text, matching rule, threshold and direction are unpublished, so our rebuild may differ from its method.
- Post hoc readings are marked: the within-layer reading of the site's checkpoint numbers, the weight check with its two extra Falcon downloads and the per-unit agreement, and the pairs against SmolLM2-135M.
- The capture was checked against the model only for SmolLM2-135M. The first run's reordered weights were not saved. The checker verified its traces instead, and its own copy's logits on 3 of 100 chunks.
- The matching-test comparison in finding e is a small synthetic network, not a language model.
- Inkling 2 Mini was not downloaded or run. Finding g is read from code.

## Disclosure

AI agents did all of the work here. Separate Claude sessions on the Opus tier wrote the derivation and ran the small networks, tried to refute the derivation with their own code, wrote the plan and ran the real models, rechecked every real-model number with code that shares nothing with the first run, surveyed prior work and then re-read it, and argued the other team's side for the outside check.

Another such session packaged this record. A person set the direction. No person has yet reviewed the numbers.

## Files

| Path | What it holds |
|---|---|
| `derivation/` | The proofs (`STATEMENTS.txt`, kept as written with private names and paths removed), exact-law routines and their brute-force checks, the symmetry checks, the site-sentence tails, the small-network code, `RESULTS.json` and the exact checks' outputs |
| `derivation/refute/` | The refuter's report (`REFUTE.txt`) and rulings (`REFUTE-RULINGS.json`), its independent exact and sampled checks, and their outputs |
| `real-models/` | `PLAN.txt` and `PLAN.sha256`, the corpus builder, capture, pairing, statistics, the two validity checks, scoring, `RESULTS.json` and the per-model and per-pair outputs |
| `real-models-check/` | The second checker's independent routines and its comparison, `out/compare.json` |
| `prior-work-check/` | The toy comparison with the matching test of Zhu and co-authors, and its output |
| `outside-check-audit059/` | [CHECK.md](outside-check-audit059/CHECK.md): our two-pass check of another team's study of the same site |
| `site_claims.json`, `anchors.json` | The site sentences we test, and the code and config facts we rely on |
