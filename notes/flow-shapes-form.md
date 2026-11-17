# Flow shapes form: what drag reduction gives the closure rule and rounding

Date: 2026-11-17
Status: idea. Not adopted.
Builds on: [closure-by-certificate](closure-by-certificate.md), [closure-counted](closure-counted.md), [closure-on-a-real-model](closure-on-a-real-model.md)
Prototype: `notes/prototypes/closure-register/closure_persist.py`
Measurements: the siliquant records named below. This note adds one small check of its own, CL-8.

## Proposal

The project owner put this forward on 2026-11-17:

```text
data should shape models as flows shape the earth

wind, water, magma; shape the earth into the ideal form for flow to pass through

in the same way data should shape models and operating systems and environments
and software and infrastructure into the ideal form to accept it and for it to
pass through and be processed optimally
```

The owner then asked which methods of drag reduction can be applied to digital systems from first principles. Two replies from an assistant came with the question. They map the proposal onto fluid mechanics, six mechanisms in all. A third document restates a paper on "neural persistence", a score of a network's weights built on the mathematics of flooding a landscape.

This note asks what of all that is mathematics, and what the records already say about it. It keeps the proposal, drops most of the mappings, and names five principles that carry over as theorems. The check of the mappings and of the persistence document, claim by claim, is in siliquant, `notes/persistence-and-flow-check.md`.

Labels: [P] proved here, [K] known, [I] a reading. The sources are listed at the end, each with how it was read.

## What drag is

Drag is the energy a flow loses for each unit it carries. A shape with less drag carries the same flow and loses less.

[I] For a model, the counterpart with real units is what a system spends for each unit of useful output: joules, or bytes of memory read, for each token at a given quality. For rounding weights it is bits per weight at a given change of the output. That last one has a proved floor, Shannon's, and siliquant keeps the table of what each part of the gap to it can be worth.

## Five principles that carry over

**1. A budget with floors.** [K] An engineer does not reduce "drag". The total is split into parts, each with its own floor, and the work goes to the largest part that is above its floor.

[P] For rounding the parts can be counted in bits per weight. At high rates no shape of cell saves more than 1.53 dB, which is 0.25 bit, and E8 saves 0.65 dB, 0.11 bit.

A scale stored in 16 bits for every 32 weights costs 0.50 bit. So the storage of scales is a larger part than everything a cell shape can give. The first two figures are in siliquant's `bounds/bounds.out`. The third is the bit count of the `Q4_0` rule.

**2. Equal gain at the margin.** [K] A wing of given span has least induced drag when the air is pushed down equally along the span. A branching vessel costs least to run when the cube of the parent's radius is the sum of the cubes of the branches (Murray's law). In both, one more unit of resource buys the same gain everywhere.

If it did not, moving a unit from a poor place to a rich one would be a free improvement. The first is due to Prandtl and Munk.

[K] The same holds for splitting bits over parts of a signal: the best split gives each part the mean rate plus half the logarithm of how much it matters, over the geometric mean (Huang and Schultheiss, 1963, and the rule called reverse water-filling). Parts under the water level get no bits at all. That is a closure with a formula.

[I] The siliquant record on gemma has the numbers this needs and has not used them. At the same 4 bits, per weight, one kind of matrix costs 52 times the KL of another. Under the principle that gap is recoverable loss. The plan in siliquant, `experiments/output-budget-gemma-e4b-2026-11-17`, tests it.

**3. Cost that grows slower than flow makes trees.** [K] When carrying twice the flow in one channel costs less than twice as much, flows merge into trunks, and the cheapest network that serves every point is a tree. River basins are the standard example (Gilbert 1967, Banavar and others 2000, Rinaldo and others 1992).

[I] This is the form of the proposal that has a theorem behind it. It does not say that training makes trees. It says what to look for: a few trunks carrying most of the flow.

The gemma record found them. One weight in 5,845 of the feed-forward output matrices lies beyond five standard deviations of its row, the ten busiest hidden units of a layer hold 2 to 24 percent of them, and pulling them back does more damage than rounding every weight to 5 bits.

**4. Noise in place of structure.** [K] A small random error can cost less than a smaller structured one. Dither is the worked case: noise added before rounding makes the error independent of the signal (Schuchman 1964). The trips that keep a boundary layer attached are the fluid case.

[I] The gemma record has one direct measurement. The same entries moved by the same amounts give a mean KL of 0.318 when all are pulled toward zero and 0.095 when each goes toward or away at random. Squared error cannot tell the two apart. The siliquant plan asks whether such a change adds up over layers where rounding does not.

**5. The best shape depends on the model of the flow.** [K] Newton's body of least resistance has a flat front, and it is best only for the flow he assumed.

[I] The gemma record: the step with the least squared error lost to the step set from the largest entry in all four cells where both were scored. The measure was wrong, not the principle. Which measure is right is the open question of [closure-on-a-real-model](closure-on-a-real-model.md).

## What the records say about the proposal itself

**The form that training leaves is not arbitrary, even where the function does not depend on it.** [I] On gemma, a move along exact symmetries, 1.6 times as long as the weights, changes the output by a mean KL of 0.00005.

Balancing through the same symmetries before rounding to 5 bits gives 5.507 where rounding the weights as trained gives 2.184. The record did not examine why. The two replies treat these symmetries as waste to remove. For rounding, on this model, the trained form was the better one.

**Weighting the error by the flow has been tried.** The activation-weighted error of the gemma record counts each weight by the mean square of the input it multiplies.

It ranked 26 scored changes with a rank correlation of 0.763, under the 0.889 of the largest singular value of the change.

**The metric the first reply proposes is the matrix G of the calibration record.** That reply takes the expected product of the Jacobian with itself as the distance in which parameters should move. `experiments/gate-metric-calibration-2026-11-15/THEORY.md` defines the same matrix.

Its distance matched the change on the probes within 1.1 on all 12 hosts, was blind to moves the probes cannot see, and was off by more than 3 on a large natural move. A proposer who knew the probes hid at least 10 times more change than they showed.

## Persistence is a flood

[K] Take a layer as a graph: one vertex for each row, one for each column, one link for each weight, carrying its size. Lower a level from the largest weight. A link appears when the level reaches its size. Separate pieces join as links appear, and the levels at which they join are the record.

Those levels are the sizes of the links of a maximum spanning tree. This is the method of the "neural persistence" paper (Rieck and others, ICLR 2019). It is also how a watershed is computed.

**It reads each unit's largest weight.** [K] The largest link at any vertex is in the tree, when it is unique: cut the vertex from the rest, and the largest link across that cut is the vertex's own largest.

So the score is mostly a statistic of each row's and each column's largest entry. On random matrices 72 to 85 percent of the tree is such an entry, and the maxima alone give 97 to 98 percent of the score (siliquant, `persist/demo.out`).

[I] The scale rule that worked on gemma sets a row's step from its largest entry. The score and the rule read the same thing.

**It cannot be a gate.** [P] The score depends only on the sizes of the weights, and on the graph up to a reordering of the rows and of the columns of each layer on its own.

So two moves leave it exactly as it was and change the function: flipping the sign of any weights, and reordering the rows of one layer without the matching reorder of the next. Each is a counterexample to "equal score, equal behaviour".

[P] The other way fails too. For a unit with a ReLU, scaling its incoming weights by a positive number and its outgoing weights by the inverse leaves every output as it was. It changes that unit's largest weight, so it changes the score. In a check on a random two-layer network the outputs agreed to 1e-15 and the score moved from 0.45 to 0.89.

So the score is constant on moves that break the function and varies on moves that keep it. Under the closure rule that ends the path "persistence as a gate on behaviour", by counterexample. It leaves open persistence as a cheap reading of where the large weights sit.

### One more sector for the register: CL-8

The closure register asks of each distance whether one radius can admit a fine-tune that passes and reject a move that breaks. CL-5 closed that for any distance between the singular-value distance and the Frobenius distance, measured after the best relabelling. A distance built on persistence is not in that range.

**The distance.** For a weight matrix, sort the sizes of its tree's links, largest first. For two cells of the same host, take the difference of the two sorted lists, layer by layer. The **largest gap** is the largest entry of those differences. The **summed gap** is the root of the sum of their squares. Biases are left out, as the paper leaves them out.

**What is proved.** [P] The k-th largest tree size is the highest level at which the graph has at most n - k pieces, n being the number of vertices. If every weight changes in size by at most e, every link present at level t in one matrix is present at level t - e in the other, so every sorted tree size moves by at most e.

The largest gap is therefore at most the largest change of any weight, which is at most the Frobenius length of the move. Reordering rows or columns changes nothing.

For the summed gap no bound is proved here. Skraba and Turner (2020, Theorem 4.8) bound a related distance between the two records by the same norm of the change. That distance may pair a level with nothing, so it can be smaller than the summed gap and does not bound it.

**Plan, written before the run.** Rebuild each of the 12 MLP hosts' passing fine-tunes as `closure_quant.py` does. Compute both gaps between the host and its fine-tune. For the breaking move, use its own length as the upper bound on its largest gap. If the breaking move can be rebuilt from the calibration record's program, compute both of its gaps exactly as well.

| Sector | Closed on a host if |
|---|---|
| One radius of a ball in the largest gap that admits the passing fine-tune and rejects a breaking move | the fine-tune's largest gap is above the breaking move's length |
| The same in the summed gap, only if the breaking move is rebuilt | the fine-tune's summed gap is above the breaking move's summed gap |

**Prediction.** The first closes on at least 8 of the 12 hosts. The second, if it can be run, on at least 10.

**Result.** Run after the plan was pushed. `closure_persist.py` rebuilt the fine-tune and the breaking move of every host, and each matches its recorded row. The figures are in `closure_persist.out`.

| | Fine-tune that passes | Move that breaks | Closed on |
|---|---|---|---|
| Frobenius length | 8.06 to 9.22 | 0.1 to 0.3 | |
| Largest gap, against the breaking move's length | 0.150 to 0.308 | at most 0.1 to 0.3 | 1 of 12 |
| Largest gap, both moves rebuilt | 0.150 to 0.308 | 0.010 to 0.026 | 12 of 12 |
| Summed gap, both moves rebuilt | 0.897 to 1.126 | 0.025 to 0.065 | 12 of 12 |

The first prediction fails: the sector closes on one host where at least 8 were predicted. The proved bound is the move's whole length, and on 11 hosts that is above the fine-tune's largest gap. The second prediction holds, on 12 where at least 10 were predicted. The third row was not a sector of the plan. It is reported because the plan had the breaking move's gaps computed.

The summed-gap sector is in the register as CL-8, certified by two exhibited moves on each host, the kind of certificate CL-2 has. The move that breaks is 15 to 45 times nearer in this distance than the fine-tune that passes.

[I] So a ball drawn in a persistence distance fails the way the Frobenius ball fails: the harmless move is the far one. A weaker distance did not help. What separates the two moves on these hosts is still their effect on the outputs, which is the path of the committed-behaviour-change record.

## The six mappings, in one table

The claim-by-claim check is in siliquant. In short:

| Mapping of the replies | What the records say |
|---|---|
| Form drag and permutation symmetry | Real for merging two trained models. CL-5 already measured distance after the best relabelling, and it gives no usable radius. |
| Boundary layers and masked adapters | No source found for the method named. Not evaluated. |
| Vortex drag and rotations | The premise is wrong: a loss on the product of weights and inputs does not change when both are rotated together. |
| Shock waves and the fold path | The fold ends at the densest packing, and rounding wants the least error. Siliquant bounds the end point at 0.35 dB. The schedule has not been run. |
| Skin friction and lookup tables | Memory read per token is a real cost. The incentre codes lose to scalar rounding at equal bits in siliquant's record of 2026-11-17. |
| Turbulence and persistence | The paper uses no cycles and prunes nothing. See the section above. |

## What stays open

- Whether bits placed by equal gain beat equal bits on a model's output. Planned in siliquant.
- Whether a structured change adds up over layers where noise does not. Planned in siliquant.
- A measure of a weight change that orders damage. Six formulas have now been named and none is a certificate. The siliquant plan adds three with their predicted failures.
- The proposal beyond models. Nothing here touches operating systems, environments or infrastructure. For those the principle with units is the second one: find where one more unit of a resource buys the most, and measure whether that is equal across the system.

## Open questions

1. Does training with a cost that grows slower than the weight make trunks, and does weight decay, which grows faster, spread them out? Principle 3 says which way to expect. Nothing here tests it.
2. The trained form rounded better than the balanced one. Is there a statement of which form is best for a given rounding rule, with a proof?
3. Can the damage of a change that all points one way be bounded over layers, where the damage of noise adds?

## Limits

- The fluid mechanics and the coding theory are standard results. Most of their sources were seen as excerpts by an agent and not opened, and one formula is from memory. The list of sources says which.
- Every number about gemma is from one model, one text and one runtime.
- The checks on persistence used random matrices and a random two-layer network.

## Sources

"Reported" means an agent opened the source and its report was read here. "Excerpt" means the agent saw a search result's text and did not open the source.

- Murray, "The Physiological Principle of Minimum Work", PNAS 12 (1926). Excerpt.
- Munk, "The minimum induced drag of aerofoils", NACA Report 121. Excerpt. The elliptical loading is also credited to Prandtl.
- Huang and Schultheiss, "Block quantization of correlated Gaussian random variables", IEEE Transactions on Communications 11 (1963). Excerpt for the paper. The rule as stated in principle 2 is from memory.
- Gilbert, "Minimum cost communication networks", Bell System Technical Journal 46 (1967). Banavar, Colaiori, Flammini, Maritan, Rinaldo, "Topology of the fittest transportation network", Physical Review Letters 84 (2000): whether loops appear depends on the convexity of the cost. Excerpt.
- Rinaldo, Rodriguez-Iturbe, Rigon and others, "Minimum energy and fractal structures of drainage networks", Water Resources Research 28 (1992). Excerpt.
- Schuchman, "Dither signals and their effect on quantization noise", IEEE Transactions on Communication Technology 12 (1964). Excerpt.
- Newton's problem of least resistance, Principia (1687). Reported, from an encyclopedia article.
- Rieck and others, "Neural Persistence", ICLR 2019, arXiv 1812.09764. Reported.
- Skraba and Turner, "Wasserstein stability for persistence diagrams", arXiv 2006.16824, Theorem 4.8. Reported.
- The siliquant records and notes named in the text, and this repository's calibration record and closure notes. Read by the session that wrote this note.

## Disclosure

Written by an AI agent session from the owner's proposal and questions of 2026-11-17, under the owner's direction.
