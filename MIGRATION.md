# Migration from weft

weft is becoming the software repository. This repository is where the research and experimentation lives. This file records what moved and how to read the older references.

## Path map

| Old path in weft | New path here |
| --- | --- |
| `docs/program/experiments/` | `experiments/` |
| `docs/program/audit/` | `audit/` |
| `scripts/corpus_audit.py` | `scripts/corpus_audit.py` |
| `scripts/test_corpus_audit.py` | `scripts/test_corpus_audit.py` |
| `scripts/test_pr116_offline.py` | `scripts/test_pr116_offline.py` |
| local razi-cells `exp/` tree (5.6 GB of generated fixtures included) | `archive/razi-cells-exp-2026-11/` (records only) |

Older records cite their own original paths (for example `docs/program/experiments/E07/...` in commands and notes). Read them with the path map. They were left as written on purpose.

## Audit tooling

`scripts/corpus_audit.py check` validates the reading ledger in `audit/` against the immutable weft commit it describes. This repository carries only the audit history, so the source snapshot stays in weft. Run it against a weft checkout:

```
python3 scripts/corpus_audit.py check --repo /path/to/weft
python3 -m unittest discover -s scripts -p test_corpus_audit.py
```

The unittest suite is pure and runs anywhere.

## Still in weft, pending a decision

- `docs/program/` at the root: charter, build program, convergence plan, experiment cards, releasing notes, work log, resume notes, decomposition, teams.
- `papers/` and the paper build pipeline.
- `docs/corpus/` (the corpus sources themselves live in weft-corpus).
- `dist-cut/`, `siliconcordat-cut/` built artifacts.

## History

Experiments and audit were migrated with git subtree split. Commits that touched those paths keep their authorship and their messages. Nothing was rewritten except this notice and the `audit/README.md` links that pointed outside the moved tree.
