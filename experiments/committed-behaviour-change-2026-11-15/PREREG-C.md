# Preregistration draft: Experiment C, splice with no input switch

Status: draft for team review. Not yet frozen, not yet run. Freezing means copying this file's predictions and file hashes into a commit pushed before any confirmatory seed is trained.

## Question

Every splice result so far leans on a handed-in context signal: an input channel or task token that says which skill is wanted. An outside router reading the same signal matches the splice (12 of 12 MLP, 20 of 20 transformer against 13 of 20). Can a packet fire on a statistic of the host's own internal state, computed inside the forward pass, where no router that sees only inputs and outputs can follow?

## Design (transformer harness of the recheck record)

The packet carries a receptor over first-layer activations. It maps a fixed statistic (windowed mean and variance of the residual stream over positions, exact form frozen at preregistration) to a gate in [0, 1]. The packet writes only when the gate is high.

Training hides the task token. Lying-token rows are included: the token names the wrong skill while the sequence statistics name the right one, and the target follows the statistics.

Arms, all at matched parameter and compute budgets, on fresh seeds:

1. Endogenous packet, spliced as in the recheck transformer record.
2. Outside router with input and output access only. It may read the full input sequence and both models' outputs. It may not read activations.
3. External adapter distilled from the same donor outputs, with the same hidden-token training.
4. Packet with the receptor ablated (gate forced open), as the always-on control.

Hosts are trained by a script the packet author does not tune on. Seeds, pilot seeds excluded, and the joint bar (native drop at most 0.025, novel at least 0.70) are frozen with file hashes before the run.

## Predictions (to be frozen)

- **C1**: the endogenous packet meets the joint bar on at least 16 of 20 fresh seeds.
- **C2**: the input-output router meets it on at most 10 of 20, because the firing statistic is not a function of the input channel it can read.
- **C3**: on lying-token rows the packet follows the internal statistic on at least 90 percent of rows.
- **C4**: the always-on control fails the native bar, showing the gate does the work.

## Kill criteria

If the router or the adapter matches the packet, packet novelty is withdrawn per issue 17. If the packet only works when a white-box router with activation access is also allowed to fail, the claim narrows to that access boundary and must be stated that way. If the receptor cannot be trained to separate the contexts at all, the endogenous route is closed on this harness.

## Disclosure

Draft written by an AI agent session with human oversight. No run in this file has happened.
