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

A network is a set of units joined by weights. A unit computes some function of the units that feed it. A weight is **open** if it is allowed to be nonzero. A **path** is a chain of open weights from an input to an output.

A family of paths that share no unit is an assignment of inputs to outputs, routed through the hidden units. The cells of the second note are the case of one layer. The **capacity** of a network is the largest number of paths in such a family.

[K] By Menger's theorem the capacity equals the size of the smallest **cut**: a set of units that every path meets. So a capacity is certified from both sides, by a family of disjoint paths and by a cut of the same size.

## Facts

**10. The outputs depend on the inputs only through a cut.** [P] Let C be a set of units that every path from an input to an output meets. Then for any weights, biases and unit functions, every output is a function of the values of the units in C.

*Proof.* Let D be the set of units v such that every path from an input to v meets C. Outputs are in D. Take v in D and not in C. It is not an input, since an input not in C is reached by a path of one unit that misses C. Every unit that feeds v is in D: a path that reached a feeder while missing C would reach v while missing C.

So, going through the units in the order of computation, each unit of D outside C is a function of units of D, and in the end of the units of C.

Three things follow, for every setting of the weights.

- The map from inputs to outputs is a map into as many numbers as C has units, followed by a second map. Where it is differentiable its Jacobian has rank at most the capacity.
- In causal terms: hold the units of C fixed, and no intervention on the inputs moves any output.
- A linear network's end-to-end matrix has rank at most the capacity.

**11. For generic weights the bound is exact.** [P] For a linear network the end-to-end matrix has rank equal to the capacity c, except on a set of weights of measure zero.

*Proof.* Take c disjoint paths. The minor of the end-to-end matrix on their inputs and outputs is a polynomial in the weights. Set the weights on the paths to 1 and all others to 0. Each chosen input then reaches its own output and no other, and the minor is 1. A polynomial that is not zero everywhere vanishes only on a set of measure zero.

The same holds for the Jacobian of a network whose unit functions are analytic with a slope that is not zero everywhere, such as tanh or GELU, at almost every setting of weights, biases and input: the minor is then an analytic function, and the same choice of weights makes it nonzero. With ReLU units the rank can be lower on a set of positive measure, because a unit can be off.

`causal_capacity.py` checks both facts on 300 random sparse networks. The capacity is certified both ways on all 300. With the cut clamped and the inputs changed, no output moves on any. The rank is at most the capacity on all 300 and equal to it on all 300, for linear, tanh and GELU units.

**12. Validity as demand against capacity.** This is a proposed definition, with one consequence proved.

- The **demand** of a task is the largest rank of the Jacobian of its target map: the number of independent directions in which an intervention on the input moves the output.
- A **structure** is a choice of which weights are open. Its capacity does not depend on the values of the weights.
- [P] A network that computes the target exactly has capacity at least the demand. This is fact 10.
- So when the capacity is under the demand, every setting of the weights on that structure is closed for exact computation. The certificate is a cut, checked by counting, and one input at which the target's Jacobian has the stated rank.

This is a closure of a different size from a ball. It closes a whole structure, with all its weight values, at once.

The proof is for exact computation. For a score within a bar it shows nothing, because the cut counts directions and not how strongly each is carried. The tests below show how far that gap reaches.

**13. Inputs the task never uses.** [P] Suppose the target does not depend on a group of inputs n, and n is independent of the other inputs. Replace a model by its average over n. Its mean squared error does not rise.

*Proof.* Fix the other inputs. The mean over n of the squared error is the squared error of the averaged model plus the variance of the model over n.

Setting the weights out of those inputs to zero is not the same as averaging. It evaluates the model at n = 0. For that the fact gives an expectation, and the test below measures it.

## Where the demand comes from

In the test world the demand can be read from the data generator. By its formula, an output of skill m depends on the input only through 4 projections of the 16 state inputs and the skill's own gate. The other 4 gates and the 3 nuisance inputs have no effect. So the demand is 5, and the generator has a cut of 5 in its own formula.

`causal_capacity.py` checks this by intervention on the generator. At 200 inputs of each of two skills the Jacobian has rank 5. The 7 unused inputs have an effect of exactly zero. Four directions are strong and the gate is weak: the fifth singular value is 0.03 of the first.

For data without a formula the demand would have to be measured by intervention. That gives an estimate and not a certificate.

## What was measured

The predictions were committed at `66783d8`, before the width and host tests ran.

| # | Prediction | Outcome |
|---|---|---|
| C1 | One skill through a layer of width 3 or less scores more than 0.025 under the dense network, on every seed | Holds |
| C2 | Width 8 or more is within 0.025 of dense, on every seed | Holds |
| C3 | The smallest width within 0.025 of dense is 4, 5 or 6 | Fails. It is 8 on all three seeds |
| C4 | Two skills need more width than one, and width 4 or less is under dense | Holds. The smallest widths are 12, 16 and 16 |
| D1 | Pruning by magnitude breaks the retention bar while the capacity is still 8 on every host | Holds |
| D2 | Closing the weights out of the three nuisance inputs lowers the native score under shift on at most 2 of 12 hosts, and moves the score without shift by less than 0.01 | Holds. The score rose on 12 of 12, with and without shift |

**The width test.** Networks 24 to 96 to c to 8 with GELU units, trained for 1,120 steps on the generator, 3 seeds. For one skill the score is 0.61 to 0.83 at width 3, 0.85 to 0.92 at width 4, 0.98 to 1.00 at width 8, and 1.00 for the dense network. For two skills it is 0.39 to 0.75 at width 4 and 0.93 to 0.96 at width 8.

**Pruning.** With half the weights of each matrix removed by magnitude, all 12 hosts fail the bar, with a drop of 0.07 to 0.12, and the capacity is still 8. The capacity first falls under 8 with 5 percent of the weights kept and under the demand of 5 with 2 percent kept. By then the score has long collapsed.

**Closing the unused inputs.** On each of the 12 hosts the 288 weights out of the three nuisance inputs were set to zero.

| Measure | Over the 12 hosts |
|---|---|
| Native score under shift | rose on 12, by 0.0025 to 0.0046 |
| Native score without shift | rose on 12, by 0.0005 to 0.0010 |
| Length of the change of weights | 3.0 to 3.6 |
| RMS change of outputs on the held-out inputs | 0.052 to 0.067 |

## Readings

[I] **The count of directions marks the first jump and not the bar.** The score jumps between widths 3 and 4, where the four strong directions first fit. Coming within the bar took width 8 for one skill, twice the number of strong directions, and 12 to 16 for two. A GELU unit passes little of a negative input, so a signed number may need two units. This was seen after the run and is not tested.

[I] **The cut does not see strength.** In a dense network the capacity stays at its ceiling long after the behaviour has failed. A certificate that counted only directions carried with a stated gain would be needed, and none is given here.

[I] **A causal closure can pass where both existing tests fail.** Closing the nuisance weights is a move 10 to 33 times longer than the breaking moves of the calibration record. It changes the outputs by more than the tolerance of 0.05 on all 12 hosts. A weight radius would reject it, and so would a tolerance on output change. It raised the score on every host.

Both tests measure distance from the present model. Where the present model responds to inputs the task never uses, that distance is partly distance from an error. A definition of validity that starts from what causes the target accepts the move, and the data bear it out on these hosts.

## What the runtime has

`synaptic_flow.py` in weft routes skill packets to free channels through a network with one unit of capacity per channel. When the demand does not fit, it returns a min-cut certificate with the shortfall, and mitosis adds that many channels. That is fact 10 and Menger's theorem applied to slots: growth is triggered by a proof that the structure cannot carry the demand.

Its demands are whole numbers supplied by the caller. Nothing derives them from the data. [I] The link the owner's second point asks for is a demand measured from the data and passed to that router.

## Limits

- **Directions, not strength.** Fact 12 closes a structure for exact computation only. The width and pruning tests show the bar is lost well before the cut says so.
- **The demand was read from a formula.** That is possible in a synthetic world. No method is given here for real data.
- **Fact 13 is proved for averaging.** For setting weights to zero it is measured, on 12 hosts of one family of worlds, with nuisance inputs of zero mean in training.
- **The width test** is one architecture, GELU units, three seeds. One of its four predictions failed.
- **Ranks are numerical**, with a threshold of 1e-10 on closed-form Jacobians and 1e-6 on the generator's, by central differences.
- **No row is added to the register.** The one closure this gives on the test world, exact computation of a skill through fewer than 5 units, is not a path anyone holds.

## Open questions

1. Is there a certificate for strength: a cut-like bound on the number of directions carried with gain at least a stated size?
2. How should a demand be measured from data that has no formula, and what would turn that measurement into a certificate?
3. Is the factor of two between demand and width the one-sidedness of the unit? A run with tanh units would say.
4. Should the gate admit a move that only closes weights out of inputs proved unused, though it exceeds both the radius and the tolerance?
5. Rounding a weight to zero closes a link. Does a rounded cell on a grid with a zero level lose capacity before it loses the bar? The pruning test suggests it does not.
