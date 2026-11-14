# Experiment records

One folder per study. Each record states its question, how it was run, what came out and its limits. A record is
evidence for what it measured and nothing more. This index is the place to start: it says what each record asks and
how far it got, so you can tell a finished result from a pilot before you open it.

## Status

| Status | Meaning |
|---|---|
| `complete` | Ran as designed, results recorded, limits stated. |
| `partial` | Some arms or stages ran. The record says which. |
| `pilot` | Small run to test a method or a mechanism. It shows direction, not a law. |
| `exploratory` | Not preregistered. Results are leads, labelled as such. |
| `design` | A protocol, proposal or prototype. Nothing in it is a measured result. |
| `withdrawn` | Kept for history. The record says why it no longer stands. |
| `superseded` | Replaced by a later record, which it names. |

The **Review** column says where the record stands with reviewers, in plain words. "Findings open" means a reviewer
raised a problem with a claim, a number or a command that the record has not yet resolved. Read those findings,
linked from the source pull request, before relying on the result. Where a reviewer finding disputes a record's own
label (for example a preregistration committed after the run), the index uses the more conservative status and the
Review column says why. Review states are as of 2026-11-14.

**Identifiers.** The E-numbers come from more than one series (the program cards in
[weft `docs/program/experiment-cards.md`](https://github.com/Moissanite-Labs/weft/blob/main/docs/program/experiment-cards.md),
the razi-cells ledger and the plasmid-grafting series), so the same E-number can name different studies. The folder
name is the identifier.

## Index

| Record | What it asks | Status | Review | Source |
|---|---|---|---|---|
| [E07/](E07/) | Razi-cells stem-cell micro-harnesses: how model choice and selection machinery affect self-improving coding agents, with a held-out audit of the archive. | `exploratory` | Reviewed in weft before the split. The fresh-seed rescore added from [weft#162](https://github.com/Moissanite-Labs/weft/issues/162) has findings open: its table matches the seed files, but three prose statements contradict them. | weft, migrated; [weft#162](https://github.com/Moissanite-Labs/weft/issues/162) |
| [razi-cells-laws-2026-11/](razi-cells-laws-2026-11/) | Which simple laws make a colony of isolated cells improve, show restraint and pass gains on (E11 to L1 of the razi-cells ledger). Guesses fixed in `TESTS.md` before data. | `exploratory` | Reviewed in weft before the split. | weft, migrated |
| [apple-silicon-swarm-2026-11/](apple-silicon-swarm-2026-11/) | E14 (program series): an Apple Silicon micro-swarm with subspace updates and horizontal transfer, and the convergence arm from [weft#118](https://github.com/Moissanite-Labs/weft/issues/118). 10 seeds. | `complete` | Reviewed in weft before the split. | weft, migrated |
| [e13-geodesic-shunting-plasmid-2026-11-12/](e13-geodesic-shunting-plasmid-2026-11-12/) | E13 (plasmid series): whether lateral shunting inhibition and geodesic retraction let a skill be spliced between independently trained 3-layer networks. 12 seeds. | `complete` | Reviewed in weft before the split. | weft, migrated |
| [weft-v2-gemini-carbon-2026-11/](weft-v2-gemini-carbon-2026-11/) | An external design proposal with a C11 and Python conformance suite for three numerical repairs to the invariant gate, plus toy simulations. | `design` | Reviewed in weft before the split. The division-free gate with a 1e-9 floor added from [weft#179](https://github.com/Moissanite-Labs/weft/issues/179) is approved. | weft, migrated; [weft#179](https://github.com/Moissanite-Labs/weft/issues/179) |
| [native-lineage-2026-11/](native-lineage-2026-11/) | Lineage selection through the live Python invariant gate: does the scored stream pick the update rule? 10 seeds. | `complete` | One finding open: the script docstring describes an earlier run's pattern. A rerun reproduces the committed results. | [weft#131](https://github.com/Moissanite-Labs/weft/issues/131) |
| [graded-chemostat-e15-2026-11/](graded-chemostat-e15-2026-11/) | E15 (program series): a graded-difficulty chemostat with a spore-fraction sweep and zero-order step cooling, on the Mac swarm harness. | `complete` | Approved. Four of eight preregistered clauses held and four failed, as the record states. | [weft#134](https://github.com/Moissanite-Labs/weft/issues/134) |
| [endogenous-cells-e16-2026-11/](endogenous-cells-e16-2026-11/) | E16 (program series): can recurrent Markov-blanket cells improve without external target supervision? Seeded run on Apple M1 Max. | `complete` | Findings open: a pinned Linux rerun flips two verdicts, so the results are host-specific; the direction of the tension controller is not stated. | [weft#135](https://github.com/Moissanite-Labs/weft/issues/135) |
| [openai-cells-blitz-2026-11-12/](openai-cells-blitz-2026-11-12/) | A $30 battery of colony experiments on OpenAI models (E18 series), with ablations and a replication. 17 hypotheses registered before the runs; the misses are reported beside the wins. | `complete` | Approved. A second reviewer's earlier change request has not been re-reviewed. | [weft#139](https://github.com/Moissanite-Labs/weft/issues/139) |
| [no-language-colony-2026-11-12/](no-language-colony-2026-11-12/) | Can cells exchange and do work without human language? Four no-language variants (E1 to E4) in three stages. | `exploratory` | Approved. A second reviewer's earlier change request has not been re-reviewed. | [weft#140](https://github.com/Moissanite-Labs/weft/issues/140) |
| [zero-lexicon-cells-2026-11-12/](zero-lexicon-cells-2026-11-12/) | E08: entities whose carrier is a matrix rather than a word, enforced at the serializer with an executable falsifier. | `exploratory` | Approved. The registered test H-E08-A was not met (p = 0.240) and is reported as such; a six-pair result is labelled post-hoc. | [weft#141](https://github.com/Moissanite-Labs/weft/issues/141) |
| [micro-cell-2026-11-12/](micro-cell-2026-11-12/) | E09: does an organism with about 800K parameters, gated by the same invariant, learn past where the small E08 actor plateaus? | `exploratory` | Approved. All three preregistered hypotheses were falsified and are reported as misses. | [weft#143](https://github.com/Moissanite-Labs/weft/issues/143) |
| [astra-family-teachers-2026-11-12/](astra-family-teachers-2026-11-12/) | Can a teacher model make persistent numerical edits to small policy cells that transfer to related siblings? Four studies, 96 archived responses. | `complete` | Approved. Exact replay holds on macOS only, as the record states. | [weft#146](https://github.com/Moissanite-Labs/weft/issues/146) |
| [e10-statistical-causality-2026-11-12/](e10-statistical-causality-2026-11-12/) | E10: scaling micro-cells (Track A, 12 seeds) and purely statistical causal and KL entities (Track B). | `partial` | Findings open: Track A reproduces exactly; Track B is named in the title but has no code or output. | [weft#147](https://github.com/Moissanite-Labs/weft/issues/147) |
| [weight-space-2026-11-12/](weight-space-2026-11-12/) | Can a strong teacher read a small model's raw weights and propose direct numerical edits? A toy flip, TinyStories probes and an NC1 suite. | `exploratory` | Findings open: the toy flip amounts to a label swap; the TinyStories claims have no committed output; preregistration verdicts are missing. | [weft#148](https://github.com/Moissanite-Labs/weft/issues/148) |
| [e11-plasmid-transfer-breaking-through-2026-11/](e11-plasmid-transfer-breaking-through-2026-11/) | E11 (plasmid series): toy horizontal transfer of a skill between networks under a null-space gate. | `pilot` | Findings open: the headline transfer is an indexing artifact (the "new" task is one the host already solves); two diagnostics are miscomputed. | [weft#150](https://github.com/Moissanite-Labs/weft/issues/150) |
| [peer-flex-harness-review-2026-11-12/](peer-flex-harness-review-2026-11-12/) | An offline review of a supplied telemetry harness ([weft#111](https://github.com/Moissanite-Labs/weft/issues/111)): which failure classes it has, each with a reproduction. | `complete` | Approved. | [weft#151](https://github.com/Moissanite-Labs/weft/issues/151) |
| [e11-ic-plasm-morphogenesis-2026-11-12/](e11-ic-plasm-morphogenesis-2026-11-12/) | E11 (morphogenesis): can 492-byte interaction-combinator graphs grow Plasm weight matrices at 64x64, 256x256 and 512x512? | `exploratory` | Findings open: the committed script does not compile; two results readouts disagree; invariants are asserted, not measured. | [weft#155](https://github.com/Moissanite-Labs/weft/issues/155) |
| [e12-plasmid-nullspace-graft-2026-11-12/](e12-plasmid-nullspace-graft-2026-11-12/) | E12 (plasmid series): grafting combinator plasmids between colonies under a Jacobian null-space gate. Preregistered, 12 seeds. | `complete` | Findings open: the gated arms use the host's true permutation and the control does not, so part of the win may be oracle alignment; the invariant results are not emitted by the script. | [weft#159](https://github.com/Moissanite-Labs/weft/issues/159) |
| [e13-transitive-plasmid-cascade-2026-11-12/](e13-transitive-plasmid-cascade-2026-11-12/) | E13 (plasmid series): three-cell transitive plasmid cascades under composed Jacobian gates. | `exploratory` | Findings open: the same oracle-alignment confound as E12; the preregistration was committed after the results; the table means do not reproduce from the committed script. | [weft#174](https://github.com/Moissanite-Labs/weft/issues/174) |
| [e14-soko-weft-colony-bridge-2026-11-12/](e14-soko-weft-colony-bridge-2026-11-12/) | E14 (soko bridge): exact-frontier optimization ported from soko to assemble a six-skill organism where greedy merging fails. 12 seeds. | `complete` | One finding open: the README checksum command fails on 4 of 5 files (the hashes themselves are right). The numbers reproduce. | [weft#169](https://github.com/Moissanite-Labs/weft/issues/169) |
| [e14_suite/](e14_suite/) | E14-Online: a preregistered adversarial drift audit with per-seed verification. | `partial` | Findings open: 2 of 10 hypotheses pass and 3 reverse, which the record does not yet state; the audit script imports modules that are not committed. | [weft#186](https://github.com/Moissanite-Labs/weft/issues/186) |
| [proof-gated-cells-2026-11-13/](proof-gated-cells-2026-11-13/) | A cell environment where a state change commits only after a pinned Lean compiler checks a certificate. A mechanism prototype. | `pilot` | No substantive findings: the theorem and the replay check out. It was held in weft for process reasons (a replay dirtied the tree; scope). | [weft#156](https://github.com/Moissanite-Labs/weft/issues/156), [weft#160](https://github.com/Moissanite-Labs/weft/issues/160), [weft#161](https://github.com/Moissanite-Labs/weft/issues/161) |
| [proof-gated-cells-e12-nullspace/](proof-gated-cells-e12-nullspace/) | A Lean 4 formalization of E12's symmetric null-space splice, with no `sorry`. | `complete` | Findings open: the proofs compile, but they use integer arithmetic and do not cover the float64 code the README connects them to. | [weft#166](https://github.com/Moissanite-Labs/weft/issues/166) |
| [stem-cell-2026-11-13/](stem-cell-2026-11-13/) | Can a teacher model propose data-only descendants of a six-integer controller that persist over two generations? | `pilot` | No substantive findings: the record reproduces. The second quiet generation overfit validation, as the record states. | [weft#160](https://github.com/Moissanite-Labs/weft/issues/160), [weft#161](https://github.com/Moissanite-Labs/weft/issues/161) |
| [verified-graft-2026-11-13/](verified-graft-2026-11-13/) | A design for verified functional grafts and routed capacity expansion. Registration only: no outcome is claimed. | `design` | No substantive findings. Regenerated fixtures are byte-identical. | [weft#161](https://github.com/Moissanite-Labs/weft/issues/161) |

## Rerunning a record written in weft

Records that came from weft were written at `docs/program/experiments/<folder>/` inside a weft checkout, and many of
their scripts find weft's code by walking up from that path (for example `Path(__file__).parents[4]`). They were left
as written. To rerun one, put the folder back at that path in a weft clone:

```bash
git clone https://github.com/Moissanite-Labs/weft.git
mkdir -p weft/docs/program/experiments
ln -s "$PWD/experiments/<folder>" weft/docs/program/experiments/<folder>
cd weft && python3 docs/program/experiments/<folder>/<script>.py
```

Commands quoted inside older records use those original paths. [MIGRATION.md](../MIGRATION.md) has the full path map.

## Adding a record

Add a folder and a row in this index with a status. CI fails if a folder has no row. What a record needs is in
[CONTRIBUTING.md](../CONTRIBUTING.md), and how it is reviewed is in [REVIEWING.md](../REVIEWING.md).
