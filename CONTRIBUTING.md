# Contributing to weft-loom

weft-loom holds the research side of [ML Weft](https://github.com/Moissanite-Labs/weft): experiment records, audits,
incident write-ups and design notes. Code that builds or runs the software goes to weft. How each kind of change is
reviewed is in [REVIEWING.md](REVIEWING.md).

## Where things go

| You have | Put it in | Index |
|---|---|---|
| An experiment, study or pilot with results | `experiments/<folder>/` | a row in [experiments/README.md](experiments/README.md) |
| A review of the codebase or its claims, with evidence | `audit/` | [audit/README.md](audit/README.md) |
| An unplanned event worth keeping | `incidents/<folder>/` | the folder's README |
| A design note, idea backlog or proposal | `notes/<name>.md` | a row in [notes/README.md](notes/README.md) |
| Code for the runtime, the site or the papers | [weft](https://github.com/Moissanite-Labs/weft) | |

Name a record folder `<short-name>-<yyyy-mm>` or `<short-name>-<yyyy-mm-dd>`. If it belongs to a numbered series,
put the series and number in the README title, not only in the folder name: E-numbers repeat across series.

## What a record needs

A README at the top of the folder with:

- **Question.** What the study asks, in one or two sentences.
- **Status.** One of the statuses in [experiments/README.md](experiments/README.md).
- **Preregistration.** A link to the plan written before the data, or the words "not preregistered".
- **How to rerun.** The command, seeds, and the machine or container it ran on.
- **Results.** The numbers, each traceable to a committed output file.
- **Limits.** Sample size, what was not controlled, and what the result does not show.
- **Disclosure.** Which parts were written or run with AI assistance.

A null or negative result is a result. Record it the same way.

## Raw data

Commit the record, the scripts and the summarised results. For bulk raw output, the rule is:

- **Up to 5 MB and 200 files per record:** commit it under the record's `data/` or `raw/` folder. GitHub collapses
  these files in pull requests (see `.gitattributes`).
- **Above that:** attach it to a GitHub release of this repository, or deposit it on Zenodo, and commit a manifest
  with each file's name, size and SHA-256 so the record can be checked against it.
- **Never:** patient or personal data, credentials, or API keys. Public literature values, synthetic data and CC0 or
  permissive datasets only.

Records migrated from weft before this rule keep their raw files as they were committed.

## Design notes

One Markdown file per note in `notes/`, with supporting files in `notes/assets/` or `notes/prototypes/`. Start with
the question or proposal, say what exists today and what does not, and list open questions. Add a row to
[notes/README.md](notes/README.md) with the status `idea` unless the team has adopted it.

## Commits

Keep the original author and date when you move work from elsewhere, and say where it came from. Nothing migrated is
rewritten to look tidier. If a file has to change on the way in (for example a name that is not valid on every
filesystem), say what changed and why in the commit and in the record.
