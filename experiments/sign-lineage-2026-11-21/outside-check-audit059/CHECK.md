# Outside check of the AUDIT-059 study of the neuron map

This is our two-pass check of another team's study of the same site, the AUDIT-059 study, filed as draft pull request 24 on Moissanite-Labs/siliquant (head commit `d4c54e43`). That study reads the site's published page data for 13 model pages and joins it to public weight files from other records.

In the first pass a reader listed eleven findings that narrow the study's claims, N1 to N11, and three points where it is strong. In the second pass an advocate argued the study's side of each finding as hard as the evidence allowed, measured what could be measured, and ruled. The advocate's rulings are final here.

Evidence kinds: *exact* means whole-number or fraction arithmetic, by two routes that must agree. *Site data* means counted from the site's published pages. *Weights* means measured on public weight files. *Sampled* means seeded random draws, with the seeds in the output. *Third party* means a number from another record, taken on trust and listed in [third_party.json](third_party.json).

## What reproduces

**1. An outside selection lands in one site family.** *Exact, site data and weights.* A public weight-edit method for Qwen3.5-0.8B picked 64 MLP units in each of layers 15 and 19. In layer 15, 16 of the 64 sit in the site's family "Adjacent brackets", against 77 of the layer's 3584 units, exact tail 8.9e-14. In layer 19 it is 4 of 64 against 11 of 3584, exact tail 2.8e-5.

"Adjacent brackets" is the single most enriched of the 297 and 292 families present in the two layers. Corrected for that many families, the tails are 2.6e-11 and 8.1e-3, so it was not picked from many. The site's kind "Equations, numbers and units" holds 22 of the 64 (1.1e-7) and 15 of the 64 (1.3e-4).

One correction to the first reader: the edit's selection is not free of activations. Its score multiplies a weight term by a difference in MLP activations on eight hand-written texts. The overlap with a family defined by firing on the site's own text is still striking, but it is not a validation by a method that never looked at activations.

**2. The enrichment survives within column blocks.** *Exact, site data and weights.* Split at the first 512 columns, the combined stratified exact tails are 3.1e-10 in layer 15 and 1.4e-3 in layer 19.

**3. Qwen3.5-0.8B's unit order is not exchangeable.** *Exact, weights and site data.* Of the 20 columns per layer with the largest single weight, 29 of 40 lie in the first seventh of the columns, exact tail 1.0e-16. In layer 15 ranks 20 and 21 tie exactly, and the other tie break gives 28 of 40, tail 1.6e-15.

The share of units outside every family is higher in the last three sevenths of columns than in the first seventh in 21 of 24 layers, two-sided sign test 2.8e-4.

Also confirmed: a copy of the Gemma 4 E4B file that the siliquant record scored, `gemma-4-E4B-it-Q8_0.gguf`, has the SHA-256 that record names, `f8854aa4480df62585a279e7ca0a881554fc18a41c59c4f62642d16a2ae47012`. So a later activation study can use the same file.

## Narrowing findings, rulings and what survives

Each item gives the finding in short, the final ruling, and the strongest surviving claim in the advocate's wording.

**N1. The chance-agreement algebra.** The study says its exact algebra reproduces the site's 83 to 87 percent agreement between unrelated Pythia and Falcon-H1 Tiny. It does so only because one input was set equal to the observed share, so it is a one-parameter fit and not a prediction.

Ruling: stands, narrowed. The advocate dropped part of the first reader's point: for gated pairs a chance rate of one half is a theorem, so the Qwen rates the study derives from the site's 93, 98 and 88 percent are correct re-expressions.

Strongest surviving claim: "If one model's neurons all point one way (p1 = 1) and the other's point the positive way with probability p2, unrelated models agree with probability exactly p2, which is arithmetically consistent with the site's own explanation of the 83 to 87% band but does not show it is the cause."

**N2. Survival inside both column blocks.** The study says the "Adjacent brackets" enrichment survives inside both blocks in both layers. At the study's own cut-off of 0.01 this holds for layer 15 only.

Ruling: stands, narrowed. Layer 19 is below 0.05 in both blocks, 0.013 and 0.028, but fails the study's own 0.01 cut-off in one block, and the other block rests on one unit.

Strongest surviving claim: "The edit's 64 selected neurons are enriched for 'Adjacent brackets' after conditioning on column block, at combined stratified exact p = 3.1e-10 in L15 and 1.4e-3 in L19."

**N3. "Dramatically more kurtotic" selected units.** The study compares the selected columns' heavy tails with all other columns, but the selection sits mostly in the first 512 columns, where heavy-tailed columns also sit.

Ruling: stands, narrowed. Against random columns matched by block, the gap survives: 42, 46 and 51 of 4000 draws reach it in layer 15, and 23, 22 and 17 in layer 19. When the draws are also matched on the weight part of the selection score, it disappears: 475 and 464 of 4000 in layer 15, 652 and 669 in layer 19.

Strongest surviving claim: "The 64 edit-selected columns per layer are more heavy-tailed than random columns with the same count per column block (sampled p about 0.01 in L15 and 0.005 in L19), a property the selection score's weight factor u @ W0 already accounts for."

**N4. "Exact dyadic 2^16 on bf16 weights".** The files hold bf16 values in float32, and the study rounds them to a grid of 2^-16, which is not exact for every entry: 13.8 and 12.2 percent of entries in the two layers lie off that grid.

Ruling: stands. It is wording only and changes no stated number.

Strongest surviving claim: "The weights are bf16 values held in float32, and every count and rank they report from them is unchanged by their 2^-16 rounding."

**N5. A Pythia trajectory "across all 3 random seeds".** The checkpoints at steps 1,000, 8,000 and 32,000 are one training run, and the other two seeds enter only at the end. The site itself says the checkpoints are one run.

Ruling: stands.

Strongest surviving claim: "In one Pythia-160m run the no-family share falls from 16.30% (step 1,000) to 3.77% (step 32,000) and ends at 5.68%, and two other seeds end at 5.36% and 5.69%, both above that run's step-32,000 value."

**N6. Gemma 4 E4B layer 10, "because" of fan-out.** The study gives a causal reason why weight statistics miss the layer whose clipping does most damage. The reason rests on a 1.3 percent lead over layer 9 in one site field, chosen after the damage was known, with no null.

Ruling: stands. Across all 42 layers the rank correlation of that field with the damage is +0.161, with a permutation p of about 0.15. The damage of layer 10 is 78.39 times the next layer's, while the field's lead is a factor of 1.013.

Strongest surviving claim: "On the site's page data, Gemma 4 E4B layer 10 ranks first of 42 in mean group out-weight (1.3% above layer 9) and is the only layer among 0 to 13 whose code share exceeds its prose share, a reasonable target for a blind test that does not explain its 78-fold clip KL."

**N7. The 21 of 21 sign test.** The study counts 21 of 21 middle layers in a window set in its code, and does not report the three layers outside it.

Ruling: stands. All three excluded layers go the other way. The substance survives on all 24 layers.

Strongest surviving claim: "In Qwen3.5-0.8B the no-family share is higher in the last three-sevenths of columns than in the first seventh in 21 of 24 layers (two-sided sign p = 2.8e-4), including every layer from 2 to 22, while layers 0, 1 and 23 go the other way."

**N8. A clean-room check that cannot be rerun.** The study's ledger says a separate check script confirmed its weight results and an unseen-seed null. That script is indexed by a hash only and is in no published branch.

Ruling: stands. The ledger's recorded details match the public weights: the tie at ranks 20 and 21 in layer 15 is at 6240 of 65536, between columns 12 and 770.

Strongest surviving claim: "The ledger describes a clean-room check whose recorded details (for example the L15 rank-20 tie at 6240/65536) match the public weights, but the check itself is not published and cannot be rerun."

**N9. A 1,000-draw permutation null.** It draws from the same sampling law as the exact tail beside it, so it checks the code but adds no evidence.

Ruling: stands.

Strongest surviving claim: "A seeded simulation of the same sampling law agrees with the exact hypergeometric tail for L15 (0 of 1,000 draws reach 16)."

**N10. Numbers not produced by the study's code.** The study's plan of next steps quotes 30 to 45 percent of units in four symbol kinds, a 7.8 to 17.2 percent share outside families, and 85 of 96 initial failures.

Ruling: stands, narrowed. The 85 of 96 is sourced in the edit's own report, but not its link to "Adjacent brackets". The four kinds hold 20.8 to 40.8 percent of units across the site's 30 models, with only 13 of 30 inside 30 to 45 percent. No site figure for the share outside families equals 7.8 or 17.2 percent.

Strongest surviving claim: "In the edit's baseline run, 85 of 96 math answers failed by running into repetition cutoffs (third-party record), and the four named symbol kinds hold 21% to 41% of neurons across the site's 30 models."

**N11. The pull request's description.** It describes only the study's other part, not the neuron study.

Ruling: stands. Housekeeping.

Strongest surviving claim: "The neuron study is committed on PR 24's head (d4c54e43) with its own README and report."

## What could not be checked

- The study's separate check script is not published, so its confirmations cannot be rerun (N8).
- The site's lineage statistic and its per-pair numbers are not published, so we cannot tell which pairs its 83 to 87 percent covers.
- 5 of the study's 15 pinned page snapshots were not read. For those the study's certificate values were used. The other 10 match copies we hold by hash.
- Heavy tails by column block in Qwen3.5-0.8B beyond layers 15 and 19, because only those two weight slices are public in the edit's repository.
- Whether the site's "Gemma 4 E4B" is the instruction-tuned file the siliquant record scored. The site does not say.

## Scripts and how to rerun

The scripts in [scripts/](scripts/) are the advocate's, cleaned of local paths. They expect the reader's own saved copies of three public pages of the site and the public files of the weight-edit repository. The pages are not included because the site states no license. [inputs.sha256](inputs.sha256) lists the hash of every input the scripts expect.

```
bash scripts/run_all.sh Q08_PAGE INDEX_PAGE GEMMA_PAGE WEM_DIR SILIQUANT_RESULTS
```

Each check runs under `python3 -I -B`, `-I -O -B` and `-I -B -W error`. Outputs were byte-identical across the three modes ([out/parity_hashes.txt](out/parity_hashes.txt)), and the `-I -B` outputs are kept in [out/](out/). The output of `adv_index_kinds.py` is not kept, because it lists the site's own figures model by model.

| Script | What it checks |
|---|---|
| `adv_exact.py` | Exact hypergeometric tails by two routes that share no arithmetic, and a stratified sum |
| `adv_page.py` | Reads the data object of a saved page as text, without running its code |
| `adv_q08_join.py` | The join of edit-selected units with site families, N2, N3 and the column order |
| `adv_q08_layers.py` | N7 per layer and N4 |
| `adv_family_scan.py` | The scan over all families present in a layer |
| `adv_gemma.py` | N6 on all 42 layers of Gemma 4 E4B |
| `adv_index_kinds.py` | N10 against the index page's kind bars |
| `adv_z2.py` | N1, the algebra, on a rational grid, with a gated block flip and a plain block control |
| `adv_extra.py` | The other tie break in item 3, the 21 of 24 sign test, and the tie value in N8 |
