# Growth by closure: a path is locked only on a proof

Date: 2026-11-15
Status: idea. Not adopted.
Prototype: `notes/prototypes/closure-register/`

## Proposal

The project owner proposed this on 2026-11-15. Speed up the growth of the system by closing every path, and every whole sector of paths, that has been tried and proved to lead nowhere. The closing is done by rule, from formulas. Even the lack of validity has to be proved formally, the way an upper or a lower bound is proved.

This note says what such a closure is, what follows from the rule, and what the project already has. It comes with a first register of closures and a program that checks them.

## What a closure is

A **path** is something the project or the system could spend effort on: a mechanism with a setting. A **sector** is a set of paths picked out by a condition.

A path is **valid** if it can meet what is asked of it. [I] Many demands in Weft come in pairs. Safety asks that a setting be small enough. Usefulness asks that it be large enough.

A **closure** is a sector together with a certificate that no path in it is valid. Two kinds of certificate are admitted.

- **Crossed bounds.** A proved upper bound `a` on a setting and a proved lower bound `b` on the same setting, with `a < b`. No value meets both. Each bound is a theorem or an exhibited object.
- **Counterexample.** The path rests on a claim about every case. One exhibited case where the claim fails ends it.

A run that found no effect is not a certificate. Nor is a control arm that matched the favoured arm, or a result that failed to reproduce. Those leave the path open, marked "not shown".

## What follows from the rule

Labels: [P] proved here, [K] known, [I] a reading.

**1. Closing on a proof loses nothing.** [K] Let `v` be the value of a path, and let the best path found so far have value at least `L`. If every closed sector has a proved upper bound on `v` that is at most `L`, the best value over all paths equals the best value over the open paths and the one already found.

Proof: a path in a closed sector has value at most its sector's bound, which is at most `L`. This is the rule that makes branch-and-bound search exact.

**2. A closure is worth the effort it removes.** [P] Suppose effort is drawn over paths with some distribution, a share `p` of it lands on valid paths, and a closed sector with no valid path held a share `m`. After closing, the share on valid paths is `p / (1 - m)`. Closing half the effort doubles it. Closing nine tenths gives ten times.

The formula assumes that the freed effort spreads over the remaining paths in the old proportions. Reading it as a speed-up of growth assumes more: that growth is proportional to the effort on valid paths, and that the certificate cost nothing to find. Neither is measured here.

[I] Two things follow. Closing a single point of a large space is worth nothing, because no effort was going to land on it again. Only sectors count. And a sector is exactly as wide as the conditions of its proof, so the way to close more is to prove the bound under weaker conditions.

**3. Given what each path needs, the closed set is computed.** [P] Let each path list what it needs: sectors, or other paths. It needs all of them, so one closed item closes it. Start from the certified sectors and add every path that needs something already closed, until nothing changes.

Proof that this is a closure operator. For a set `S` of closed items, let `F(S)` be the union of three sets: `S`, the certified sectors, and the paths that need a member of `S`. `F` never removes anything, and a larger `S` or more certificates give a larger result.

There are finitely many paths, so repeating `F` from the empty set stops at a set that `F` leaves unchanged. That set contains every certified sector. With more certificates each step of the repetition is at least as large, so the result is too. And starting again from the result adds nothing, because it already holds every path that needs one of its members.

What a path needs is written by hand. That list is a judgement, and every path the program closes rests on it. Only the step after it is mechanical.

**4. A move that changes behaviour too much closes a ball around itself.** [P] Theorem 1 of the calibration record bounds how far the outputs of the E13 three-layer net can move inside a ball of weight space. Its proof uses only quantities at the centre of the ball, so it holds at any centre.

Call a move failed if it changes the outputs on a set of inputs by more than a tolerance `tau`, in RMS. That is a different test from the retention bar, which is a score.

Take a failed move `d*` with change `D*`. For every move within distance `rho` of `d*`, the change is at least `D* - B(rho)`. Here `B(rho)` is the RMS over the inputs of the theorem's bound, with its constants taken at `w0 + d*`. Every move inside the radius where `B(rho) < D* - tau` has failed too. The same argument around a move known to be within tolerance gives a ball of moves proved within tolerance.

[I] For a short failed move the closed radius is close to `(D* / tau - 1)` times the radius proved within tolerance around the baseline, because the same linear term of the bound sets both. In the output the two agree within 1 percent at length 0.1 and within 5 percent at length 0.3. Beyond that the formula runs high, by 19 to 27 percent at length 1 and by more than double at length 3.

Either way, a move that failed badly closes far more than the baseline's safe ball holds.

`closure_balls.py` computes both on the 12 MLP hosts with `tau = 0.05`. It works in double precision, not in interval arithmetic.

| Ball | Radius |
|---|---|
| Proved within tolerance around the baseline | 0.00265 to 0.00313 |
| Closed around a failed move of length 0.1 | 0.015 to 0.018 |
| Closed around a failed move of length 1, about one training step | 0.17 to 0.20 |
| Closed around a failed move of length 3 | 0.48 to 0.54 |

For lengths from 0.1 to 3 the closed radius is 0.15 to 0.20 of the length of the failed move. Along the 22 directions the program tried from the edge of each closed ball, the change stays over the tolerance, as the theorem says it must. [I] The smallest of those changes is 0.08 against a tolerance of 0.05, which suggests the proved ball is smaller than the true region.

**5. Closures copy themselves under symmetry.** [P] A permutation of the hidden units of a layer, applied alike to the weights into and out of that layer, changes the weights and leaves every output as it was. It maps a failed set of weights to another failed set, since failing depends only on the outputs.

The constants of Theorem 1 are the largest singular values of two weight matrices and the lengths of the hidden activations. A permutation changes none of them, so the closed ball has the same radius at the image. One failed move closes a ball at every image. The images lie far from the baseline: the permutation in the record moves the weights by 28 to 30 on the MLP hosts.

## Why only proofs

[I] The two errors do not cost the same. A dead path left open wastes the effort that lands on it. A live path closed by mistake is lost for good, and the best path may be inside it.

The project met both on 2026-11-15.

- The thread record said a reversal skill cannot be spliced until an attention graft exists. Nothing proved it. In the recheck record a packet of 16,576 weights at the first layer's position-wise block reached the skill on 8 of 8 seeds, with attention frozen and the native skills kept.
- In the same recheck, 70 of the 71 review findings that had a direction claimed more than the evidence. [I] The prose leans toward keeping paths alive. A register of closures is the counterweight: the place where "this cannot work" is written down with its proof.

## What the project already has

- **A certificate that drives growth.** `weft/runtime/plasm/synaptic_flow.py` returns a min-cut certificate with every routing of demands to slots. When the demand exceeds what the present network can route, the certificate proves the shortfall. A verifier rebuilds the network and the flow, and `total_demand - max_flow` is the number of channels that mitosis adds. This is crossed bounds in exact arithmetic: a proved ceiling on flow below the demand.
- **A dual certificate for probes.** `identifiability_gate.py` uses an exact Farkas dual to bound how well the probes can tell a real change of skill from a bias, and adds probes when they cannot. It is adapted from another project and covered here by tests only.
- **What a ball can separate.** The safety gate rejects every move outside a ball. At the shipped radii of 10 and 120 the breaking moves of the calibration record, of length 0.1 to 0.3, are inside the ball and admitted. A radius small enough to reject them also rejects the fine-tunes that pass the bar (6.0 to 9.2) and the permutations that change nothing (17 to 30).
- **A proved bound.** Theorem 1 of the calibration record gives a radius inside which no output of the E13 net moves by more than a stated amount. It is loose.
- **A claim one input can refute.** The committed-behaviour-change record admits a graft as a claim about behaviour and lets any single input overturn it. Each refutation there is a counterexample certificate.
- **No register of closed paths.** Dead ends sit in prose inside records. The claims register in weft lists what is verified, and the recheck found 10 of its 14 "verified" rows stale or false.

[I] The proposal extends the first of these from slots to every path.

## A first register

`notes/prototypes/closure-register/closures.json` holds the four closures below, three more from [closure-counted](closure-counted.md), one sector that was closed without proof and is open, and ten paths. `check_closures.py` checks each certificate against the numbers the records saved and exits with status 1 if one fails. Its last output is `check_closures.out`.

The checker does not rebuild the moves behind those numbers. `closure_balls.py` rebuilds one class of them, the adversary's moves on the MLP hosts, and checks each against its recorded row. `closure_quant.py` rebuilds the fine-tunes of the MLP hosts for the later closures. For the four closures below, the fine-tunes, the grafts, the hidden moves of CL-3 and the transformer moves are read as recorded.

| Id | Sector closed | Upper bound | Lower bound | Certified on |
|---|---|---|---|---|
| CL-1 | One radius for the linear Plasm cell that admits the drift of its full training run and holds output change to 5 percent | 0.127, exact | 0.463 | the cell |
| CL-2 | One radius of the Frobenius ball that admits a passing fine-tune and rejects a breaking move | 0.1 to 0.3 | 6.0 to 9.2 | 24 of 24 hosts |
| CL-3 | A threshold on a probe set the proposer can see, that admits a passing graft and rejects a breaking move | 0.044 to 0.18 | 0.171 to 0.245 | 11 of 11 hosts with a passing graft |
| CL-4 | The two-check admission rule as the whole admission test | counterexample | 37 of 181 admitted grafts fail the bar | 478 grafts |

- **The gap in CL-2.** The exhibited fine-tune is 27 to 90 times longer than the exhibited breaking move. That is a property of the two moves shown, and a shorter passing move may exist. [I] It suggests how badly a ball fits the shape of the safe region.
- **Where CL-1 stays live.** The bounds meet at a tolerance of 18.2 percent. The upper bound is exact. The lower bound is the drift of the full unconstrained run, and the cell learns part of the way inside smaller radii, as the next point shows.
- **What a 5 percent bound still admits.** In Paper 1's own runs a radius of 0.127 admits the first generation of the cycle (drift 0.103 to 0.104 over 10 seeds) and not the second (0.160 to 0.162). Those numbers are in weft, `papers/01-models-as-cells/results.json`, and the checker does not read them.
- **Paths these close**, each only as far as its certificate reaches. Finding one radius for the Plasm cell that keeps its full training run and a 5 percent bound. Tuning one radius of the ball on the 24 calibration hosts. Admitting grafts on a published fixed probe set, on the 11 hosts certified. Shipping the two-check rule as the whole admission test.

The certificates of CL-2 and CL-3 are recorded moves, measured in double precision. The thinnest margin is MLP host 3, where the breaking move lowers the score by 0.0254 against a bar of 0.025.

## What stays open

These looked dead in the recheck. None has a bound, so none is closed.

| Path | What the recheck found | What would close it |
|---|---|---|
| E15 dual morphogenesis as evidence for its mechanism | An arm with the same information and no mechanism also passes 12 of 12 | A proof that the benchmark cannot separate the two arms |
| E11 plasmid transfer between independently trained networks | A readout-only arm scores 0.705 against 0.703. With the true alignment handed over, the plasmid arm leads, 0.806 against 0.736 | A proof that transfer by unit index carries nothing across a random relabelling of units |
| Dormant units as the place to splice | 13 of 20 against 12 of 20 in random units | A bound on the difference |
| Score display as a colony law | The effect is +0.543 with one task and -0.019 without it | Nothing formal is in sight. It needs the run the power calculation asks for |

## Open questions

1. How much effort do the four closures remove? Fact 2 needs the share `m`, which nobody has measured. A count of the open issues, pull requests and planned runs that need a closed sector would give a first number.
2. How often does a proposer land inside a closed ball? Fact 4 gives the radius. The share depends on where proposals fall, and a gate that kept the list of failed moves could measure it.
3. Can a sharper bound than Theorem 1 sort single moves into proved within tolerance, proved failed and undecided? It needs a bound on the second-order term.
4. Do CL-2 and CL-3 hold beyond toy scale? Each needs only two exhibited moves per model.
5. Should cells in a colony read the register before they act? The price runs show that a list changes first acts, and a register of dead approaches is a list.
6. Where should the register live once adopted, and should CI run the checker?

Questions 1 and 2 are taken up in [closure-counted](closure-counted.md), for uniform proposals.
