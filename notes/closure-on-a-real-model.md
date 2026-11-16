# Closure on a real model: what a first day on Gemma says about the rule

Date: 2026-11-15
Status: idea. Not adopted.
Builds on: [closure-by-certificate](closure-by-certificate.md), [closure-counted](closure-counted.md) and [closure-causal-capacity](closure-causal-capacity.md)
Data: the siliquant record [model-output-gemma-e4b-2026-11-15](https://github.com/Moissanite-Labs/siliquant/blob/main/experiments/model-output-gemma-e4b-2026-11-15/README.md)

## Why this note

The three closure notes tested the rule on small networks built for the purpose. On 2026-11-15 the project owner asked for experiments on real models first, with theory to follow the data.

This note reads one day of measurements on `gemma-4-E4B-it`, a language model of 7.5 billion weights, for what they say about closure. The measurements, the program and their limits are in the siliquant record. Every number here is from its `results.out`.

The model's output is scored against the unchanged model on 10,200 positions of text. The score is the mean KL divergence between the two next-token distributions, and the share of positions where the top token stays the same. The unchanged model scores 0.000000 and 99.99 percent against its own saved outputs.

## What closed exactly

| Closure | Certificate | Holds for | Weights | Mean KL | Top token kept |
|---|---|---|---|---|---|
| Rows of the per-layer token table for tokens that do not occur | The table is read by row. A row whose token is absent is on no path from input to output. | inputs made of the 2,207 tokens of the text | 2,794,842,624 | 0.000000 | 99.99 % |
| Keys and values of the last 18 layers | Those layers reuse an earlier layer's keys and values. The forward pass that llama.cpp builds never reads their own. | every input | 55,050,240 | 0.000000 | 99.99 % |
| Moves along three exact symmetries | Each is an identity of the forward pass: one factor is scaled up and the factor it meets is scaled down. | every input | 3,633,315,840 moved by 1.6 times their length | 0.000047 | 99.93 % |

The first two rows score as the unchanged model does on every printed digit. The first is 37.2 percent of the model's weights.

One closure that looks the same did not hold. Zeroing the same rows of the main token table gives a mean KL of 1.364. That table is read by row at the input, and the same weights are the output layer. A weight with two uses is closed only when both are off the path.

## Three readings for the rule

**A cut closes weights where the graph has a lookup or an unread branch, and nowhere else.** Fact 10 of the causal-capacity note says outputs depend on inputs only through a cut. On this model it gives the closures above. In the 294 dense matrices of the blocks every unit is on a path, the capacity is full, and the capacity test of fact 12 closes nothing.

**Distance in weight space does not order damage.** The move along the symmetries is 4.09 dB larger than the weights themselves and changes almost nothing. Pulling back the 0.015 percent of weights that lie beyond five standard deviations of their row is a change of -42.85 dB and gives a mean KL of 0.200, with the top token kept on 87.12 percent of positions. The harmless change is 47 dB larger than the harmful one.

No ball in weight space separates the two, whatever its radius. The second note showed a ball closes a negligible share of a high-dimensional cell. The third found a harmless closure longer than the breaking moves on twelve small hosts. The real model shows the same at a scale of 47 dB.

**A region to close must be drawn in the model's own terms.** The three closures that held are a set of rows, a set of tensors and a set of orbits. None is a neighbourhood of a point.

## What a strength certificate has to explain

The causal-capacity note ended on an open question: a certificate for how strongly a direction is carried. The real model sets the terms.

- **A thin sprinkling of large weights carries far more than its size.** The 188,362 entries of the feed-forward output matrices beyond five standard deviations of their row are one weight in 5,845. Pulling them back gives a mean KL of 0.164. They sit in every layer, and in no layer do ten hidden units hold more than 24 percent of them.
- **The direction of a change matters, not only its size.** Pulling the largest 0.17 percent of weights toward zero gives a mean KL of 0.318. Moving the same weights by the same amounts in random directions gives 0.095.
- **Three formulas were tested and none is a certificate.** Squared error, and an error weighted by the gains and partner matrices along the forward pass, do not rank the changes. The largest singular value of the change ranks the 23 variants that round (rank correlation 0.92). It has the two clip probes as 4.6 and 9.6 dB better than a rounding that does less damage than either.

Two of the three were written before their data and are scored as failed predictions in the record.

So the certificate is still missing. What the data adds is a test set for the next attempt: 56 scored changes to one model, with the harmless and the harmful ones known.

## Limits

- One model, one text of documentation and source code, one runtime. The closure of the unread keys and values is a fact about llama.cpp's forward pass at commit `427291b`.
- The reference is an 8-bit file. Changed weights are stored as 16-bit floats.
- The symmetric move leaves one position of 10,200 with a KL of 0.43. Whether the float format causes it was not checked.
- Nothing was added to the closure register. Its checker recomputes every certificate from committed data, and an 8 GB model file cannot be committed.
- Which of the large weights matter, and why, is not known. Only their count by layer, row and column was looked at.

## Open questions

- Is there a formula, read from the weights alone, that ranks the fifty changes by their measured damage?
- Do the same closures and the same sensitivity hold on the other models on the machine (Ornith, Qwen)?
- Can the register hold a closure whose certificate needs a file too large to commit, for example by naming the file's SHA-256 and the command that checks it?
