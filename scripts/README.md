# scripts

Tooling for the research records in this repository.

- `corpus_audit.py`: inventory an immutable weft commit and validate the reading ledger in `audit/`. See `MIGRATION.md` for how to run it.
- `test_corpus_audit.py`: regression checks for the ledger validator. Pure unittest, no network, no repo data.
- `test_pr116_offline.py`: offline regression checks for the PR #116 review fixes on the heldout audits in `experiments/E07/`.
