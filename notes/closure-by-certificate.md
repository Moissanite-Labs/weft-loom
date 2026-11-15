# Growth by closure: a path is locked only on a proof

Date: 2026-11-15
Status: idea
Prototype: `notes/prototypes/closure-register/`

## Proposal

The project owner proposed this on 2026-11-15. Speed up the growth of the system by closing every path, and every whole sector of paths, that has been tried and proved to lead nowhere. The closing is done by rule, from formulas. Even the lack of validity has to be proved formally, the way an upper or a lower bound is proved.

This note says what such a closure is, what follows from the rule, and what the project already has. It comes with a first register of closures and a program that checks them.

## What a closure is

A **path** is something the project or the system could spend effort on: a mechanism with a setting. A **sector** is a set of paths picked out by a condition.

A path is **valid** if it can meet what is asked of it. In Weft most demands come in pairs. Safety asks that a setting be small enough. Usefulness asks that it be large enough.

A **closure** is a sector together with a certificate that no path in it is valid. Two kinds of certificate are admitted.

- **Crossed bounds.** A proved upper bound `a` on a setting and a proved lower bound `b` on the same setting, with `a < b`. No value meets both. Each bound is a theorem or an exhibited object.
- **Counterexample.** The path rests on a claim about every case. One exhibited case where the claim fails ends it.

A run that found no effect is not a certificate. Nor is a control arm that matched the favoured arm, or a result that failed to reproduce. Those leave the path open, marked "not shown".

## What follows from the rule

Labels: [P] proved here, [K] known, [I] a reading.

**1. Closing on a proof loses nothing.** [K] Let `v` be the value of a path, and let the best path found so far have value at least `L`. If every closed sector has a proved upper bound on `v` that is at most `L`, the best value over all paths equals the best value over the open paths and the one already found.

Proof: a path in a closed sector has value at most its sector's bound, which is at most `L`. This is the rule that makes branch-and-bound search exact.

**2. A closure is worth the effort it removes.** [P] Suppose effort is drawn over paths with some distribution, a share `p` of it lands on valid paths, and a closed sector with no valid path held a share `m`. After closing, the share on valid paths is `p / (1 - m)`. Growth speeds up by the factor `1 / (1 - m)`. Closing half the effort doubles the rate. Closing nine tenths gives ten times.

[I] Two things follow. Closing a single point of a large space is worth nothing, because no effort was going to land on it again. Only sectors count. And a sector is exactly as wide as the conditions of its proof, so the way to close more is to prove the bound under weaker conditions.

**3. The closed set is computed.** [P] Let each path list the sectors it needs open. Given a set of certificates, call a path closed if it lies in a certified sector or needs one, and apply the rule until nothing changes.

The result contains every certified sector, grows when certificates are added, and does not change when the rule is applied again. That makes it a closure operator in the usual sense. No judgement enters after the certificates are in.

**4. A failed move closes a ball around itself.** [P] Theorem 1 of the calibration record bounds how far any output can move inside a ball of weight space. Take a move `d*` already shown to change behaviour by `D*` on a set of inputs, and a tolerance `tau`.

For every move within distance `rho` of `d*`, the change is at least `D* - B(rho)`, where `B(rho)` is the theorem's bound taken at `w0 + d*`. Every move inside the radius where `B(rho) < D* - tau` is therefore over the tolerance too. The same argument around a move known to be safe gives a ball of safe moves. Neither radius has been computed yet.

## Why only proofs

[I] The two errors do not cost the same. A dead path left open wastes the effort that lands on it. A live path closed by mistake is lost for good, and the best path may be inside it.

The project met both on 2026-11-15.

- The thread record said a reversal skill cannot be spliced until an attention graft exists. Nothing proved it. The recheck record reached reversal accuracy 1.0 with every attention weight frozen, on 10 of 10 seeds. Under the rule of this note that sector would never have been closed.
- In the same recheck, 70 of the 71 review findings that had a direction claimed more than the evidence. [I] The prose leans toward keeping paths alive. A register of closures is the counterweight: the place where "this cannot work" is written down with its proof.

## What the project already has

- **Certificates that drive growth, for one resource.** `weft/runtime/plasm/synaptic_flow.py` emits a min-cut certificate when the demand for slots exceeds what the present network can route. A verifier rebuilds the network and the flow. The shortfall, `total_demand - max_flow`, is the number of channels that mitosis adds.
- **The same for probes.** `identifiability_gate.py` does the like with an exact Farkas dual, adapted from another project and covered here by tests only. Both certificates are crossed bounds in exact arithmetic: a proved ceiling below a required amount. The proposal extends that operation from slots and probes to every path.
- **A gate that closes by distance.** The safety gate rejects every move outside a ball. The calibration record shows what that closes. Fine-tunes that pass the bar and permutations that change nothing lie outside the ball, and moves that break the bar lie inside it.
- **A proved bound.** Theorem 1 of the calibration record gives a radius inside which no output moves by more than a stated amount. It is loose.
- **A claim one input can refute.** The committed-behaviour-change record admits a graft as a claim about behaviour and lets any single input overturn it. Each refutation there is a counterexample certificate.
- **No register of closed paths.** Dead ends sit in prose inside records. The claims register in weft lists what is verified, and the recheck found 10 of its 14 "verified" rows stale.

## A first register

`notes/prototypes/closure-register/closures.json` holds four closures, one sector that was closed without proof and is open, and six paths. `check_closures.py` recomputes each certificate from the committed data files and exits with status 1 if one fails. Its last output is `check_closures.out`.

| Id | Sector closed | Upper bound | Lower bound | Certified on |
|---|---|---|---|---|
| CL-1 | One radius for the linear Plasm cell that admits its own training drift and holds output change to 5 percent | 0.127, exact | 0.463 | the cell |
| CL-2 | One radius of the Frobenius ball that admits a passing fine-tune and rejects a breaking move | 0.1 to 0.3 | 6.0 to 9.2 | 24 of 24 hosts |
| CL-3 | A threshold on a probe set the proposer can see, that admits a passing graft and rejects a breaking move | 0.044 to 0.18 | 0.171 to 0.245 | 11 of 11 hosts with a passing graft |
| CL-4 | The two-check admission rule as the whole admission test | counterexample | 37 of 181 admitted grafts fail the bar | 478 grafts |

- **The gap says how far off the path was.** In CL-2 the lower bound is 27 to 90 times the upper bound. A measure that could work has to be that much tighter along the directions that break the model than along the ones that train it.
- **The same bounds say where a path is live.** In CL-1 the two bounds meet at a tolerance of 18.2 percent. Above that the window of valid radii is known exactly.
- **Paths these four close:** presenting radius 120 as a 5 percent bound for the Plasm cell, tuning the radius of the ball, admitting grafts on a published fixed probe set, and shipping the two-check rule as the whole admission test.

The certificates of CL-2 and CL-3 are exhibited moves, measured in double precision. The thinnest margin is MLP host 3, where the breaking move lowers the score by 0.0254 against a bar of 0.025.

## What stays open

These looked dead in the recheck. None has a bound, so none is closed.

| Path | What the recheck found | What would close it |
|---|---|---|
| E15 dual morphogenesis as evidence for its mechanism | An arm with the same information and no mechanism also passes 12 of 12 | A proof that the benchmark cannot separate the two arms |
| E11 plasmid transfer between independently trained networks | A readout-only arm scores 0.705 against 0.703 | A proof that transfer by unit index carries nothing across a random relabelling of units |
| Dormant units as the place to splice | 13 of 20 against 12 of 20 in random units | A bound on the difference |
| Score display as a colony law | The effect is +0.543 with one task and -0.019 without it | Nothing formal is in sight. It needs the run the power calculation asks for |

## Open questions

1. How much effort do the four closures remove? The factor in fact 2 needs the share `m`, which nobody has measured. A count of the open issues, pull requests and planned runs that need a closed sector would give a first number.
2. How large are the balls of fact 4 on the E13 hosts, against the length of one training step?
3. Can a sharper bound than Theorem 1 sort single moves into proved safe, proved harmful and undecided? It needs a bound on the second-order term.
4. Do CL-2 and CL-3 hold beyond toy scale? Each needs only two exhibited moves per model.
5. Should cells in a colony read the register before they act? The price runs show that a list changes first acts, and a register of dead approaches is a list.
6. Where should the register live once adopted, and should CI run the checker?
