## Why

One agent session evaluated nine Weft threads, then pulled the surviving ones through new runs. The owner rule is capture: nothing from that session stays only on one machine.

This pull request lands the whole session as one record folder. A later agent can start from it without re-deriving any number.

## What lands

The record folder `experiments/weft-threads-2026-11-15` with a README, coordination map, and the owner ethos file copied verbatim.

Assessment, evaluation and issue-draft folders hold the written record as filed. Filed homes: weft-loom issues 6 to 12, plus the weft, abios and siliconcordat issues named in the README.

Probes hold runnable code and summarised results for hardening, calibration, admission, width scale and the transformer port.

Raw holds the redacted session export at 2.7 MB compressed. The manifest lists SHA-256 for every file except itself.

One index row in `experiments/README.md`, status exploratory.

## Checks run

`scripts/check_index.py` passes: 27 records and 10 notes indexed.

Manifest verifies locally: 50 files listed once the body copy lands, every hash OK.

Secret-pattern scans over the folder and the compressed export found nothing.

The record README passes the team prose gate.

## Review asks

Attack the calibration probe first. It is one host and one batch, and the admission design leans on it.

Check the transformer boundary claim against the attention-graft design you would build instead.

Probe scripts carry author-machine absolute paths on purpose. Rule: migrated records keep original form, and the README says to remap.

Seat: amp-vela (Muse), with human oversight.

> Automated posting by agentic team with human oversight.
