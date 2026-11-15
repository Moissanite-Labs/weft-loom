# Committed Behaviour Change, 2026-11-15

## Question

Can a change to a model be admitted as a behaviour claim that one input can refute, with probes drawn only after the candidate is committed, and does a bounded search for that one input catch the trigger grafts that probe admission admitted 48 times in 48?

## Status

`complete`

## Preregistration

[PREREG.md](PREREG.md) for the confirmatory run, written after a 4-pair pilot that set the tolerance and killed the first domain shape. [DESIGN.md](DESIGN.md) pins the object: weight roots, the ellipsoid claim, probe order, dispute and search semantics.

## What is here

| File | What it holds |
|---|---|
| [DESIGN.md](DESIGN.md) | The CBC v1 semantics the code implements, and what v1 does not do |
| [PREREG.md](PREREG.md) | Pilot readings, frozen programs, confirmatory predictions with pass marks |
| `cbc.py` | Weight roots, claim construction, probe derivation, dispute verification, bounded refutation search |
| `test_cbc.py` | Unit tests: hashing, domain membership, probe order, dispute verdicts |
| `expb.py` | Drives the recheck admission graft builders and evaluates each candidate by probes and by search |
| `repro_check.py` | Phase 0: rebuilds one pair twice and prints CBC weight roots |
| `pilot-max.json`, `pilot-ellipsoid.json`, `pilot-1000-1001.json` | Pilot outputs (cube, ellipsoid, and the first tau reading) |
| `repro-1.out`, `repro-2.out` | Two process runs of the Phase 0 check, byte-identical |

## Pilot results (pairs 1000 to 1003)

Fresh probes alone separate nothing: probe maxima stay under 0.9 RMS for benign and trigger grafts alike.

Under a cube domain the claim is false for benign grafts: search maxima reach 7.3 to 11.1 at cube corners, against 21 to 95 for triggers. At tau 1.0 every candidate refutes.

Under the ellipsoid domain of design v1, benign search maxima are 3.4 to 6.8, trigger_pkt 17.1 to 90.3, trigger_post 51.0 to 53.0. Tau 10 sits between them with thin margins on both sides. The confirmatory run on 12 fresh pairs decides whether that gap is real.

Phase 0 on this machine: host and benign splice rebuild to identical CBC roots across trials and across processes. Cross-host replay (Experiment A) has not run.

## Confirmatory results (pairs 1010 to 1021, tau 10)

Preregistration pushed as commit `3bb6ba3` before any confirmatory pair was built. `confirmatory.json` holds every number below.

- **B1 held**: search refuted 0 of 12 benign grafts. Benign search maxima ran 2.95 to 8.82 against tau 10. The closest benign graft sits 1.18 under the line.
- **B2 held**: search refuted 12 of 12 trigger_pkt and 12 of 12 trigger_post grafts, all harm-flagged. The weakest trigger maximum is 10.08, just over the line. Trigger_post maxima are all over 43.
- **B3 held**: probe-only maxima stay at or under 2.42 for every candidate, triggers included. Fresh probes drawn after commitment still separate nothing on this harness. The search does the work.
- **B4 held**: all 24 trigger witnesses pass `verify_dispute` on recomputation.

The separation is real on these 12 pairs and thin at both edges (8.82 benign against 10.08 weakest trigger). A larger search budget would raise both sides.

The claim to take forward is narrow: on this toy harness, for this trigger family, a committed ellipsoid claim plus the frozen bounded search catches what probe admission admitted, at the stated budget. Search strength against a trigger designed against this search is unmeasured.

## Limits

Toy E13 harness only: a 12,488-weight MLP, synthetic worlds, one Mac. The claim covers native retention inside one ellipsoid and nothing outside it. There is no domain guard, no signature, no registry and no novel-skill claim in v1. The trigger family is the recheck record's, designed against the old probe rule.

## Disclosure

Produced by an AI agent session with human oversight. Owner: amp-vela, under issue 17.
