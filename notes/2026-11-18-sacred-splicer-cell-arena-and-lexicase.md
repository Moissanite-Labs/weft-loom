# Spliceware: a cellular substrate and an anchor gate

Date: 2026-11-18
Status: idea. Not adopted.
Owner: ahrazzle
Source: [`Moissanite-Labs/spliceware`](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/docs/INDEX.md), branch `consolidate/sacred-splicer-synthesis`, commit `c1329b2`. The session it records was captured by mithrax-exo in November 2026.
Experiment: [`experiments/2026-11-18-c11-triangular-sum-lexicase/`](../experiments/2026-11-18-c11-triangular-sum-lexicase/README.md)

Marks: **source claim** means the spliceware corpus says it, and this note checked it only by reading that corpus and the C11 files at the commit above. **proposed** means this note suggests it and nothing has measured it.

## The question

Weft offers a candidate weight cell to a gate and commits it or not. Spliceware runs a search over cells in C11 and states that one common ranking rule fails badly. Does that failure apply to weft, and is the fix worth copying?

## What weft has today

In weft, a capability edit is a candidate cell of weights offered to the ball gate. It commits when `||W_cand - W_base||_F <= R_INVARIANT` with `R_INVARIANT = 120.0`, and when the metabolic budget precondition `budget >= cost > 0` holds. Both are read from `weft/runtime/invariants/` in [the SC-WSP note](scwsp-directional-gate.md) §2, which also records the combined gate as a prototype rather than an adopted design.

Two bounds, one on distance and one on cost. Neither of them asks what the cell does.

## What spliceware states

Spliceware collapses a Rust and Wasm stack into one packed C11 atom. The corpus holds five synthesis documents, a verbatim session capture and four compilable generations under `substrates/c11/`. Its central object is a cell of 1,088 bytes.

The cellular mechanics are in [Era IV](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/docs/04-cellular-substrate-and-sacred-splicer.md). The priors and the gate are in [Era V](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/docs/05-adaptive-priors-and-lexicase-selection.md).

| Mechanism | What the corpus states | Where |
|---|---|---|
| 1,088-byte Cell | `left[32]` and `right[32]` hold Merkle links. `body[1024]` holds a header and payload. One 256-bit ARX sponge hashes the whole cell, and an open-addressed arena indexes cells by hash. The cell fits one UDP datagram under a 1,472-byte MTU. `RAM == WIRE == HASH`: the memory image, the wire format and the hash preimage are the same bytes. | Era IV |
| Zero-net stack seams | Crossover happens only at program counters where cumulative stack depth is back to zero (`Δsp == 0`). A load-time scan through an Opcode Valence Table `(arity_bytes, delta_sp)` keeps cuts off instruction boundaries, so a spliced child cannot slice a 2-byte immediate or a 33-byte hash. Entropy for the cut point comes from the parent hashes and the tick, so peers replay the same evolution. | Era IV |
| Mitosis `0xFFFF` | A fork marker runs the cell as two branches, `ancestor_a` and `ancestor_b`, and an A/B fuel tournament picks the survivor. A missing hash traps into a fault cell that marks the gap instead of aborting the tick. | Era IV |
| In-cell priors | An adaptive prior vector (`HDR_WEIGHTS`) lives inside `Cell.body`. Multiplicative updates (`adapt_prior`) raise the sampling weight of codons in winning strands, inside the child cell. The search prior travels on the wire with the genome instead of sitting in an external controller. | Era V |
| Anchor gate | Eight bytes in the body carry four `(input, expected output)` pairs. Every arriving cell checks itself against them, with no external test packets and no arena lookup. See the [proposals document](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/docs/proposals/2026-11-lexicase-and-triangular-sum.md) for the specification and the two tiers below. | proposals |

The corpus states one hazard plainly. A tournament that ranks by fuel alone has a degenerate winner: `0x00` HALT at the code start burns no fuel and takes every round. A rigid all-or-nothing test suite fails the other way, because a valid two-step mutation dies when its first step breaks an assertion. Either rule alone is broken, by opposite failure modes.

The proposal pairs the anchors with two selection tiers:

| Tier | Rule as written | Role |
|---|---|---|
| Tier 1, canonical promotion | Strict 4/4 anchors, plus a better fuel margin | Promote to champion and broadcast the cell. Keeps the primary lineage from regressing or collapsing. |
| Tier 2, stepping-stone pool | At least 3 of 4 anchors | Admit the near miss as the second breeding partner. Keeps partial loop scaffolds and adapted priors alive for the next splice. |

## Why the hazard reaches weft

Weft's gate has no behavioural term. A cell that changes almost nothing can pass it, because its drift stays inside the ball and its cost can sit at the smallest positive value the budget allows. Nothing in the gate asks what changed in behaviour.

If a weft search ranks candidates by cost alone, the near-empty edit is the strongest candidate it can produce, for the same reason `0x00` HALT wins a fuel tournament. The corpus's argument is that cost ranking needs a behavioural floor in front of it.

Four kinds of work follow, all **proposed**:

1. Put the behavioural check beside the ball, not inside it. Distance and cost stay as they are. The check answers a separate question: does this cell still do the thing its claim says.
2. Carry the probes with the claim. Spliceware gets self-verification for free because the checks ride inside the cell that is also the hash and the wire packet. A weft cell carries weights, so the equivalent is a small probe set attached to the capability record and checked at commit time.
3. Keep a second tier. A candidate that passes three of four probes and costs less is not worthless. It is a donor for the next edit, and discarding it is how a search loses the middle of a long jump.
4. Measure the collapse before copying the fix. A weft run that ranks by cost alone, on a real checkpoint, would say whether the near-empty edit wins outside a toy.

## The anchor ladder

The four anchors are the values of the triangular sum `T(n) = n(n+1)/2 mod 256` at four inputs.

| `n` | `T(n)` | `T(n) mod 256` | Anchor |
|---:|---:|---:|---|
| 0 | 0 | 0 | `(0, 0)` |
| 5 | 15 | 15 | `(5, 15)` |
| 13 | 91 | 91 | `(13, 91)` |
| 37 | 703 | 191 | `(37, 191)` |

Two properties carry the design. A fixed chain of `ADD` instructions cannot hit both `n = 5` and `n = 37`, so straight-line unrolling of the loop fails the suite. That is what forces real iteration. And `(0, 0)` is passed by a program that emits zero for zero, which gives trivial strands a foothold and lets `adapt_prior()` see a winner early instead of starving in a suite that returns nothing.

Source claim: the ladder defeats unrolling and leaves a gradient. It is an argument from the instruction set, not a measurement. The experiment folder beside this note tests the gate arithmetic, not the evolution.

## How the gate reads in the C11 code

In [`v3_evogenesis.c`](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/substrates/c11/v3_evogenesis.c) at this commit, `score_anchors()` runs each anchor input through the cell and counts exact matches modulo 256. A candidate with `cand_anchors >= 3` enters the arena and becomes `ancestor_b`. Promotion to champion needs `strictly_better && (cand_anchors == 4 || cand_anchors > champ_anchors)`, where `strictly_better` compares anchor count first and total anchor error second.

The comments above that block label the 3/4 pool as Tier 1 and the 4/4 promotion as Tier 2, which inverts the naming in the proposal document. Read the test, not the comment.

The same comparison order is what stops a cheaper near miss from taking the crown: anchor count comes first, and cost is never the primary key.

[`v4_unigenesis.c`](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/substrates/c11/v4_unigenesis.c) moves the same idea into a 64-byte header with an 8-word prior vector and anchor words at indices 14 and 15. Generation-by-generation provenance is in the [C11 changelog](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/substrates/c11/CHANGELOG.md).

## Limits

- Nothing here is measured on real weights. No checkpoint, no weft model, no training run. Every claim about weft comes from reading repo notes.
- The substrate is a C11 sketch. Its arena holds 16,384 cells, its stack is 64 entries and its fuel cap is 512 steps. None of those numbers transfer to weft.
- No weft runtime change is proposed. This note does not touch `weft/`, `workers/` or the runtime code.
- The experiment harness scores five hardcoded byte strings through a stub evaluator. It shows the gate rule operating. It cannot show that evolution finds the anchors, and it does not run the spliceware VM.
- The anchors are 8-bit and the comparison is modulo 256. A probe set on weight cells would need wider values and a tolerance.
- One capture, one author. The corpus is a transcript of a single session by mithrax-exo. Nothing in it has been independently reproduced.

## Open questions

- Would a cost-ranked weft search actually produce the near-empty edit as winner, or does some other term in the score already prevent it?
- Which four probes would carry an anti-unrolling property for a weight cell, where the unit is a tensor update and not a bytecode loop?
- Does the second tier help on a real search, or does it slow the tournament by keeping cells that never contribute?
- Does the probe set belong on the cell, on the capability record, or in the ledger? Spliceware gets self-verification from `RAM == WIRE == HASH`, and a weight cell does not have that property.
- What plays the role of fuel in weft: wall time, FLOPs, energy, or the metabolic budget the gate already takes?
