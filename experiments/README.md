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
linked from the source pull request, before relying on the result.

**Identifiers.** The E-numbers come from more than one series (the program cards in
[weft `docs/program/experiment-cards.md`](https://github.com/Moissanite-Labs/weft/blob/main/docs/program/experiment-cards.md),
the razi-cells ledger and the plasmid-grafting series), so the same E-number can name different studies. The folder
name is the identifier.

## Index

| Record | What it asks | Status | Review | Source |
|---|---|---|---|---|
| [E07/](E07/) | Razi-cells stem-cell micro-harnesses: how model choice and selection machinery affect self-improving coding agents, with a held-out audit of the archive. | `exploratory` | Reviewed in weft before the split. | weft, migrated |
| [razi-cells-laws-2026-11/](razi-cells-laws-2026-11/) | Which simple laws make a colony of isolated cells improve, show restraint and pass gains on (E11 to L1 of the razi-cells ledger). Guesses fixed in `TESTS.md` before data. | `exploratory` | Reviewed in weft before the split. | weft, migrated |
| [apple-silicon-swarm-2026-11/](apple-silicon-swarm-2026-11/) | E14 (program series): an Apple Silicon micro-swarm with subspace updates and horizontal transfer, and the convergence arm from weft#118. 10 seeds. | `complete` | Reviewed in weft before the split. | weft, migrated |
| [e13-geodesic-shunting-plasmid-2026-11-12/](e13-geodesic-shunting-plasmid-2026-11-12/) | E13 (plasmid series): whether lateral shunting inhibition and geodesic retraction let a skill be spliced between independently trained 3-layer networks. 12 seeds. | `complete` | Reviewed in weft before the split. | weft, migrated |
| [weft-v2-gemini-carbon-2026-11/](weft-v2-gemini-carbon-2026-11/) | An external design proposal with a C11 and Python conformance suite for three numerical repairs to the invariant gate, plus toy simulations. | `design` | Reviewed in weft before the split. | weft, migrated |

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
