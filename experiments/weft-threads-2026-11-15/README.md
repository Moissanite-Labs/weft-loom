# Weft threads evaluation and thread-pulling, 2026-11-15

## Question

Where has Weft tread meaningful new ground, what would outsiders value, and which threads repay pulling to a decisive test?

## Status

`exploratory`

## Preregistration

Not preregistered. Several probes state pass and fail bars in their docstrings, written before their runs on the same day. Treat those as local discipline, not external preregistration.

## What is here

`WORKSPACE.md` is the coordination map: repos, thread status, convergences, checkpoint.

`ethos.md` is the team capture rule this record follows. It arrived as an owner file and is copied verbatim.

`assessment/` holds the first value assessment verbatim, plus the issue body as filed and its readback.

`evaluation/` holds the nine-thread workflow results, the workflow script, skeptic probes, and issue readbacks.

`issues/` holds every issue draft as filed. The filed record sits in weft-loom issues 6 to 12, weft 210, abios 52 and siliconcordat 15 to 16.

`probes/` holds runnable probe code and summarised result JSON files. Each number in issues 10 and 11 traces to one of them.

`raw/` holds the redacted session export, gzip compressed. It was made with `muse export --redacted` near the end of the session.

`MANIFEST.sha256` lists every file in this folder with its SHA-256. It covers all files except itself.

## Headline results

No thread counts as new ground yet. The ranked verdicts sit in `WORKSPACE.md` and siliconcordat issue 16.

Wire-only splice passes 12 of 12. Distinct worlds pass 11 of 12. At 160,520 parameters the splice passes 6 of 6.

On a 272,384-parameter transformer, a position-wise skill spliced into dormant neurons scores 1.0 on all skills. A reverse skill fails in every arm.

Shipped gate radii accept 47 of 48 grafts at radius 120 and 0 of 48 at radius 10. Two behavior checks cover every harmful class tested.

A content router cannot work in the E13 world. Content is drawn the same for every skill there.

## How to rerun

Probes ran on one Apple Silicon Mac, macOS, 2026-11-15. Code reading bound to weft snapshot `1f8b611` from 2026-11-08 and a loom snapshot from 2026-11-13.

Probe scripts carry local absolute paths from that machine. Remap the paths at the top of each script before running elsewhere. Nothing was rewritten to hide this.

MLP probes need Python 3 with NumPy: `python3 probes/hardening.py`, and likewise for the other probe names.

Transformer probes need CPU PyTorch. Recreate the environment (not committed, regenerable):

```
python3 -m venv .venv-torch
.venv-torch/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv-torch/bin/python probes/tf_splice3.py
```

Seeds are fixed inside each script. Colony live runs were not repeated. Feasibility used the harness kit selftest only.

## Limits

Toy tasks only. Transformer arms ran 2 to 3 seeds. The transformer packet trained on true labels as a donor proxy, and the donor solves its tasks.

GitHub main code was read for issue state, not line by line. Findings bind to the snapshots named above.

The session export ends just before the commit that carries it. The pull request itself is the record of the last steps.

Excluded as regenerable: the PyTorch venv and Python bytecode caches. Excluded by rule: credentials and personal data. A secret-pattern scan ran before commit.

## Disclosure

This record was produced by an AI agent seat (amp-vela, Muse) with human oversight. Evaluation children ran as subagents under the script in `evaluation/`.

Team seats were invited over the Divan Bus at seq 1676 and notified of results at seq 1677 and 1678. No seat replies had arrived at last check.

> Automated posting by agentic team with human oversight.
