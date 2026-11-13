# weft-loom

The research and experimentation hub for [weft](https://github.com/Moissanite-Labs/weft).

weft is the software: the runtime, the tooling, the site, the releases. This repository is where the science lives. Experiment records, preregistrations, raw results, audits, incident write-ups, and the reasoning behind the code. If a file exists to test an idea or record what was learned, it belongs here. If it exists to build or run the software, it stays in weft.

## Layout

- `experiments/`: experiment records, one folder per study, with preregistrations, results, and limits stated as prominently as findings. Migrated from weft with history.
- `audit/`: reviews of the codebase and its claims, with the evidence attached.
- `incidents/`: unplanned events worth keeping, with captured evidence and what was done about it.
- `scripts/`: the tooling that validates the records.
- `archive/`: records imported from the operator's local run trees, minus generated bulk fixtures.
- `MIGRATION.md`: how this repository was carved out of weft, and how to read older references.

## Rules

1. No patient data, ever. Public literature values, synthetic data, and CC0 or permissive datasets only.
2. Every record states its limits. A small arm shows direction. It does not settle a law.
3. Migrated content keeps its original authors and dates. Nothing is rewritten to look tidier.
4. Where results depend on a person's local layout, say so in the record. Do not present a folder as reproducible when it is not.

## Relationship to weft

weft links here instead of carrying the records inline. Code may cite an experiment folder here. It may not duplicate it. Releases of the software are weft's business. What the releases claim, and how the claims were checked, is documented here.
