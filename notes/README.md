# Design notes

Ideas, proposals and design backlogs for ML Weft. A note says what could be built or tested and why. It is not a
result: nothing in a note has been measured unless it links a record in [experiments/](../experiments/README.md).

Notes may disagree with each other. When the team adopts one, its status changes to `adopted` and the notes it
replaces become `superseded`.

| Status | Meaning |
|---|---|
| `idea` | Proposed by its author. Not adopted. |
| `proposal` | Put forward for a decision, with a concrete next step. |
| `adopted` | The team agreed to build or test it. |
| `superseded` | Replaced by a later note, which it names. |
| `withdrawn` | Kept for history. The author no longer proposes it. |

How notes are reviewed is in [REVIEWING.md](../REVIEWING.md) (idea lane): a note is checked for speculation stated
as fact and for wrong statements about existing code, not for evidence.

## Index

| Note | What it proposes | Status | Owner | Date | Review |
|---|---|---|---|---|---|
| [scwsp-directional-gate](scwsp-directional-gate.md) | A directional gate for weight updates: a projection test beside the distance ball, drawn from the SC-WSP brief in ethos. | `idea` | ahrazzle | 2026-11-14 | One finding open: the II-B spec adds an undefined gamma term that conflicts with the note's own gate stack. From [weft#187](https://github.com/Moissanite-Labs/weft/issues/187). |
| [horizon-ii-dual-plane-silicon](horizon-ii-dual-plane-silicon.md) | Dual-plane silicon and compute-in-memory as a Horizon II extension, mapped onto C2 and the 64-byte telemetry frame. | `idea` | ahrazzle | 2026-11-14 | Approved, with wording comments. From [weft#188](https://github.com/Moissanite-Labs/weft/issues/188). |
| [horizon-ii-verified-causal-substrate](horizon-ii-verified-causal-substrate.md) | A formally verified causal substrate as the Horizon II endgame (II-B, II-C). | `idea` | ahrazzle | 2026-11-14 | Finding resolved on the move here: a commutation statement said "iff" where only "if" holds; it now says "if". From [weft#189](https://github.com/Moissanite-Labs/weft/issues/189). |
| [horizon-ii-ideas-backlog](horizon-ii-ideas-backlog.md) | An inventory of the hardware-track ideas, with one canonical invariant and where each idea would first be tested. | `idea` | ahrazzle | 2026-11-14 | Finding resolved on the move here: row 15 said no watermark tool exists; it now names `verify_watermark_retention` in weft's plasm. From [weft#190](https://github.com/Moissanite-Labs/weft/issues/190). |
| [horizon-ii-bio-causal-substrate](horizon-ii-bio-causal-substrate.md) | An inventory of biological analogies for causal substrates. Explicitly not an architecture. | `idea` | ahrazzle | 2026-11-14 | Approved, with comments. From [weft#191](https://github.com/Moissanite-Labs/weft/issues/191). |
| [horizon-ii-grounded-codesign-loop](horizon-ii-grounded-codesign-loop.md) | A grounded co-design loop between Horizon I software and Horizon II hardware, using the telemetry frame and the gate. | `idea` | ahrazzle | 2026-11-14 | Approved, with wording comments. From [weft#192](https://github.com/Moissanite-Labs/weft/issues/192). |
| [horizon-ii-silicon-tinker-sandbox](horizon-ii-silicon-tinker-sandbox.md) | A sandbox rung for trying silicon ideas against the Metal harness before any hardware (Rung B). | `idea` | ahrazzle | 2026-11-14 | Approved, with comments. From [weft#193](https://github.com/Moissanite-Labs/weft/issues/193). |
| [horizon-ii-kernel-adapter-harness](horizon-ii-kernel-adapter-harness.md) | A verifiable kernel and adapter harness around the invariants and telemetry code. | `idea` | ahrazzle | 2026-11-14 | Approved, with comments. From [weft#194](https://github.com/Moissanite-Labs/weft/issues/194). |
| [causal-ir-externalized-tokenizer](causal-ir-externalized-tokenizer.md) | An externally typed causal IR with a harness delaborator, as a bridge between Horizon 0 and Horizon I. | `idea` | ahrazzle | 2026-11-14 | Two findings open: an unqualified "cannot misrepresent" claim that the next note contradicts; the figure's licence differs from the docs licence (CC BY 4.0). From [weft#195](https://github.com/Moissanite-Labs/weft/issues/195). |
| [2026-11-14-causal-ir-v0](2026-11-14-causal-ir-v0.md) | An audit of the abios-ir v0.1 prototype in `prototypes/`, read against the causal-IR note. | `idea` | ahrazzle | 2026-11-14 | One finding open: the stated fix is overstated; an unchecked initial state prints `[verified]`. From [weft#196](https://github.com/Moissanite-Labs/weft/issues/196). |
| [closure-by-certificate](closure-by-certificate.md) | Close a path, or a whole sector of paths, only on a formal certificate: two proved bounds that cross, or a counterexample. With a register of closures, four from this note, and a program that checks them against recorded data and closes the paths that need them. | `idea` | ahrazzle | 2026-11-15 | Not yet reviewed. Written up by an agent session from the owner's proposal. |
| [closure-counted](closure-counted.md) | What closed cells force and what they are worth when paths are assignments, why closing by balls is a covering problem, and three more sectors tested on the calibration hosts: a gate that ignores relabelling, a gate around a rounded cell, and a proved ball against a grid step. | `idea` | ahrazzle | 2026-11-15 | Not yet reviewed. Written up by an agent session from the owner's list of concepts. |
| [closure-causal-capacity](closure-causal-capacity.md) | Paths, assignments and weights as one object. A network carries at most as many independent causal directions as its smallest cut of units, and exactly that many for generic weights with linear or analytic units. Validity proposed as the task's demand against that capacity. Five of six predictions held. The cut did not predict where the score meets the bar. Closing the weights out of unused inputs raised the score on all 12 hosts, by under 0.005. | `idea` | ahrazzle | 2026-11-15 | Not yet reviewed. Written up by an agent session from the owner's three directions. |

The ten notes dated 2026-11-14 say "Not adopted" in their own header. They were written as one series, and the review state above is
from the latest review on each source pull request as of 2026-11-14. Paths such as `docs/design-notes/<name>.md`
inside a note refer to the note's original place in weft; the note is now `notes/<name>.md` here.
