# Closure by causal capacity: validity as demand against a cut

Date: 2026-11-15
Status: idea. Not adopted.
Builds on: [closure-by-certificate](closure-by-certificate.md) and [closure-counted](closure-counted.md)
Prototype: `notes/prototypes/closure-register/causal_capacity.py`

## Why this note

The second note treated three kinds of path apart: a move of weights, an assignment, a research direction. On 2026-11-15 the project owner answered that they are one thing, and gave three directions.

1. The weights represent the assignment and the assignment is in the weights. All action is derived from the weights.
2. The ground is causality. If the parameters are causally shaped, what remains is the data that goes in.
3. Validity must itself be defined and derived by formula, so that it too is causally bound.

This note gives the three a form that can be checked, proves what it can, and tests the rest. The facts continue the numbering of the earlier notes. Labels: [P] proved here, [K] known, [I] a reading.

## One object

A network is a set of units joined by weights. It is feed-forward: the units can be put in an order of computation in which each unit is a function of earlier ones. A weight is **open** if it is allowed to be nonzero. A **path** is a chain of open weights from an input to an output.

A family of paths that share no unit is an assignment of inputs to outputs, routed through the hidden units. The one-to-one assignments of the second note are the case of a single layer. The **capacity** of a network is the largest number of paths in such a family. A network with every weight open has the capacity of its narrowest layer.

[K] By Menger's theorem the capacity equals the size of the smallest **cut**: a set of units that every path meets. So a capacity is certified from both sides, by a family of disjoint paths and by a cut of the same size.

## Facts

**10. The outputs depend on the inputs only through a cut.** [P] Let C be a set of units that every path from an input to an output meets. Then for any weights and biases, and any unit functions, every output is a function of the values of the units in C.

*Proof.* Let D be the set of units v such that every path from an input to v meets C. Outputs are in D. Take v in D and not in C. It is not an input, since an input not in C is reached by a path of one unit that misses C. Every unit that feeds v is in D: a path that reached a feeder while missing C would reach v while missing C.

So, going through the units in the order of computation, each unit of D outside C is a function of units of D, and in the end of the units of C. A unit that no input reaches is a constant.

Three things follow.

- In causal terms: hold the units of C fixed, and no intervention on the inputs moves any output. This needs nothing of the unit functions.
- If the unit functions are differentiable, the Jacobian of the map from inputs to outputs has rank at most the capacity, at every input. Without that condition the bound can fail, because one unit could then pack two numbers into one.
- A linear network's end-to-end matrix has rank at most the capacity.

**11. For generic weights the bound is exact.** [P] For a linear network the end-to-end matrix has rank equal to the capacity c, except on a set of weights of measure zero.

*Proof.* Take c disjoint paths. The minor of the end-to-end matrix on their inputs and outputs is a polynomial in the weights. Set the weights on the paths to 1 and all others to 0. Each chosen input then reaches its own output and no other, and the minor is 1. A polynomial that is not zero everywhere vanishes only on a set of measure zero.

The same holds for the Jacobian of a network whose unit functions are analytic with a slope that is not zero everywhere, such as tanh or GELU, at almost every setting of weights, biases and input. The minor is then an analytic function. It is nonzero for the weights above, with biases and an input that put every unit on the paths where its slope is not zero.

With ReLU units the rank can be lower on a set of positive measure, because a unit can be off.

`causal_capacity.py` checks both facts on 300 random sparse networks. The capacity is certified both ways on all 300. With the cut clamped and the inputs changed, no output moves on any. The rank is at most the capacity on all 300 and equal to it on all 300, for linear, tanh and GELU units.

**12. Validity as demand against capacity.** This is a proposed definition, with one consequence proved.

- The **demand** of a task on an open set of inputs is the largest rank its target map's Jacobian takes there: the number of independent directions in which an intervention on the input moves the output.
- A **structure** is a choice of which weights are open. Its capacity does not depend on the values of the weights.
- [P] Let the unit functions be differentiable. If a network agrees with the target on an open set of inputs, its capacity is at least the demand on that set. This is fact 10. Agreement on the data points alone proves nothing.
- So when the capacity is under the demand, every setting of the weights on that structure is closed for exact computation on that set. The certificate is a cut, checked by counting, and one input in the set at which the target's Jacobian has the stated rank.

This is a closure of a different size from a ball. It closes a whole structure, with all its weight values, at once.

It has two limits that the tests below make plain. The proof is for exact computation, and the cut counts directions without regard to how strongly each is carried. And the demand is a rank at a point, so it does not count what a network must hold to switch between skills that live in different regions of the input.

**13. Inputs the task never uses.** [P] Suppose the target is a function of the other inputs only, a group of inputs n is independent of them, and second moments are finite. Replace a model by its average over n. Under that same law of n, its mean squared error does not rise.

*Proof.* Fix the other inputs. The mean over n of the squared error is the squared error of the averaged model plus the variance of the model over n.

Setting the weights out of those inputs to zero is a different thing. It evaluates the model at n = 0, and the fact is silent on that. Nor does the fact cover a test in which the law of n has shifted. For both, the test below is a measurement and nothing more.

## Where the demand comes from

In the test world the demand can be read from the data generator. By its formula, an output of skill m depends on the input only through 4 projections of the 16 state inputs and the skill's own gate. The other 4 gates and the 3 nuisance inputs do not enter. So the demand of one skill is 5, and the generator has a cut of 5 in its own formula.

`causal_capacity.py` measures this by intervention on the generator itself: each of the 24 inputs is moved in turn and the generator is run again. At 200 inputs of each of two skills the Jacobian has rank 5. Moving any of the 7 unused inputs changes no output. Four directions are strong and the gate is weak: the median fifth singular value is 0.02 to 0.03 of the first.

For data without a formula the demand would have to be estimated by intervention. That gives an estimate and not a certificate.

## Terms for the tests

- The **hosts** are the 12 MLP networks of the calibration record (`experiments/gate-metric-calibration-2026-11-15`): 24 inputs, two hidden layers of 96 GELU units, 8 outputs, trained for 280 steps on two skills. Every weight is open, so their capacity is 8, the number of outputs.
- The **native score** of a host is its R2 on those two skills under the record's shifted test inputs. The **bar** is a drop of at most 0.025 in it.
- The **held-out inputs** are 2,048 unshifted inputs per host, 1,024 for each of its two skills. The earlier notes use a **tolerance** of 0.05 on the RMS change of the outputs over them.
- A **breaking move** is a move found by a search that tries to do damage. Its length is the shortest tested length, 0.1 or 0.3, at which the search breaks the bar.
- In the width test the score is R2 on 1,024 fresh unshifted inputs per skill.

## What was measured

The predictions were committed at `66783d8`, before the width and host tests ran. They are judged on the longer of two training lengths, as the program's header fixed.

| # | Prediction | Outcome |
|---|---|---|
| C1 | One skill through a layer of width 3 or less scores more than 0.025 under the dense network, on every seed | Holds |
| C2 | Width 8 or more is within 0.025 of dense, on every seed | Holds |
| C3 | The smallest width within 0.025 of dense is 4, 5 or 6 | Fails. It is 8 on all three seeds |
| C4 | Two skills need more width than one, and width 4 or less is under dense | Holds. The smallest widths are 12, 16 and 16 |
| D1 | Pruning by magnitude breaks the bar while the capacity is still 8 on every host | Holds |
| D2 | Closing the weights out of the three nuisance inputs lowers the native score on at most 2 of 12 hosts, and moves the score without shift by less than 0.01 | Holds. The score rose on 12 of 12, with and without shift |

**The width test.** Networks 24 to 96 to c to 8 with GELU units, 3 seeds, one run per cell. With 1,120 training steps and one skill, the mean score at widths 1, 2, 3, 4, 5, 6 and 8 is 0.35, 0.49, 0.69, 0.89, 0.85, 0.94 and 0.98. The dense network scores 1.00.

The climb is gradual and not always upward: width 5 scores under width 4 on two of three seeds. Width 8 is the first within the bar on every seed, and one seed clears it by 0.004. For two skills the score is 0.39 to 0.75 at width 4 and 0.93 to 0.96 at width 8.

With 280 steps, the hosts' own recipe, the smallest width within the bar is 16, 96 and 96 for one skill and 96 on every seed for two. So the width at which the bar is met depends on how long the network is trained.

**Pruning.** With half the weights of each matrix removed by magnitude, all 12 hosts fail the bar, with a drop of 0.07 to 0.12, and the capacity is still 8. On the host that loses it first, the capacity falls under 8 with 5 percent of the weights kept and under 5 with 2 percent kept. By then the score has long collapsed. The hosts serve two skills, so 5 is only a lower bound on what they need.

**Closing the unused inputs.** On each of the 12 hosts the 288 weights out of the three nuisance inputs were set to zero.

| Measure | Over the 12 hosts |
|---|---|
| Native score, under shift | rose on 12, by 0.0025 to 0.0046 |
| Score on the held-out inputs, without shift | rose on 12, by 0.0005 to 0.0010 |
| Length of the change of weights | 3.0 to 3.6 |
| RMS change of outputs on the held-out inputs | 0.052 to 0.067 |

## Readings

[I] **Nothing in the scores marks the demand.** A layer of width 4 has capacity 4, under the demand of 5, and still scores 0.85 to 0.92. The score climbs through the demand without a step.

[I] The bar was met at width 8, about twice the four strong directions, on three seeds with one run each. That may be the unit, which passes little of a negative input, or the training, or chance. The definition of fact 12 did not predict where the bar is met.

[I] **The cut sees neither strength nor switching.** In a dense network the capacity stays at its ceiling long after the behaviour has failed. And two skills needed 12 to 16 units where the demand, a rank at a point, is still 5. A certificate that counted directions carried with a stated gain, across regions of the input, would be needed. None is given here.

[I] **Closing unused inputs did no harm and a little good, where a small weight radius and the output tolerance would refuse it.** The move is 3.0 to 3.6 long. A weight radius small enough to reject the breaking moves, 0.1 to 0.3, would reject it. The shipped radii of 10 and 120 would admit it.

[I] It also changes the outputs by more than the tolerance of 0.05 on all 12 hosts, narrowly on one. The score rose on every host, by under 0.005.

[I] Both tests measure distance from the present model. Where the present model responds to inputs the task never uses, part of that distance is distance from an error.

This shows less than it may seem. The rule applied is "close the weights out of inputs proved unused". It is a different rule from the capacity test of fact 12, which also lets through the pruning that breaks the bar. Whether any causal rule turns harmful moves away is not tested here.

## What the runtime has

`synaptic_flow.py` in weft assigns skill packets to free channels of one layer, each channel used at most once, by a max-flow computation. When the demands do not fit, it returns a min-cut certificate with the shortfall. A separate function, which the caller applies, adds that many channels.

That is the argument behind Menger's theorem, on one layer of slots. It proves that the slots cannot hold the packets. It says nothing about what the network can compute, which is the subject of fact 10.

Its demands are whole numbers supplied by the caller. Nothing derives them from the data. [I] The link the owner's second point asks for is a demand measured from the data and passed to that router.

## Limits

- **Directions, not strength or switching.** Fact 12 closes a structure for exact computation only, and its demand is a rank at a point. The width and pruning tests show the bar is lost well before the cut says so.
- **The demand was read from a formula** and confirmed by intervention on a generator that can be run at will. No method is given here for real data.
- **Fact 13 is proved for averaging under one law of the unused inputs.** Setting weights to zero, and the test under shift, are measured only, on 12 hosts of one family of worlds.
- **The width test** is one architecture, GELU units, three seeds, one run per cell. One of its four predictions failed, and its answer changes with training length.
- **Ranks are numerical.** A singular value counts if it is over 1e-10 of the largest for the networks' Jacobians, and over 1e-6 of the largest for the generator's, which is taken by central differences. The rank of a linear network's matrix uses an absolute threshold of 1e-9.
- **No row is added to the register.** The one closure this gives on the test world, exact computation of a skill through fewer than 5 units, is not a path anyone holds.

## Open questions

1. Is there a certificate for strength: a cut-like bound on the number of directions carried with gain at least a stated size?
2. How should a demand be measured from data that has no formula, and what would turn that measurement into a certificate?
3. What sets the width at which the bar is met? A run with tanh units, more seeds and longer training would separate the unit from the training.
4. Should the gate admit a move that only closes weights out of inputs proved unused, though it exceeds a small radius and the tolerance?
5. Rounding a weight to zero closes a link. Does a rounded cell on a grid with a zero level lose capacity before it loses the bar? The pruning test suggests it does not.
