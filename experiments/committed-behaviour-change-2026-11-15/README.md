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
| `replay_splice.py`, `decisions-1000.json`, `packet-1000.bcpp` | Recorded-artifact replay: recorded slot lists and packet wire bytes, float32 roots |
| `cbc2.py`, `test_cbc2.py` | Design v2 code: float32 roots, decisions bound into the claim id, domain guard. V1 in `cbc.py` is untouched |
| `followup.py`, `followup.json` | Adversarial follow-ups: benign at larger budget, two-column AND trigger |
| `lit_search.py`, `lit-search.out`, [LITERATURE.md](LITERATURE.md) | The arXiv prior-art search for the two novelty stakes |
| [PREREG-C.md](PREREG-C.md) | Experiment C draft: splice with no input switch. Not frozen, not run |
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

## Follow-ups (exploratory, designed after the confirmatory reading)

`followup.json` from `followup.py`, same 12 pairs:

- Benign grafts at roughly 7 times the search budget: 1 of 12 crosses tau (pair 1015, best 10.002). The other 11 stay at or under 7.20. So the ellipsoid claim at tau 10 is false as a universal statement for at least one benign graft. Admission held because the frozen budget stopped short of the witness.

  Anyone can still dispute that graft with the witness input. That is the design working as intended, and the admission reading was overstated.
- A search-aware trigger that needs two nuisance columns high at once (about 4.1 sd each, harm 18 to 19 RMS against its amplitude-0 control): the frozen search refutes 12 of 12, maxima about 48. The one-column-at-a-time sweep is not the weak point here, because the random stage seeds the hill climb with jointly high rows.

Experiment A, first cross-host reading (`crosshost-43758319377.txt`): every runner agrees with itself across trials, and no two hosts share a CBC root. Float32 host weights are identical on all three hosts.

The benign splice matches between this Mac and Ubuntu. On the GitHub macOS runner it takes a different discrete path (8006 of 12488 float32 entries differ). Bit-exact replay fails as written.

Two more dispatches localize and fix it. The packet itself diverges on that runner, in extraction, while the host root matches. When replay instead consumes the recorded packet wire bytes and the recorded slot lists, under float32 roots, it matches on all three hosts (`replay_splice.py`, run 43759282824).

So cross-host replay holds when the record carries its artifacts and discrete decisions. Recomputing them from seeds is retraining, not replay. Hashing float64 weights still makes even agreeing hosts disagree, so the root belongs over canonical float32 bytes.

`PREREG-C.md` is the Experiment C draft (splice with no input switch), not yet frozen or run.

## Limits

Toy E13 harness only: a 12,488-weight MLP, synthetic worlds, one Mac. The claim covers native retention inside one ellipsoid and nothing outside it. There is no domain guard, no signature, no registry and no novel-skill claim in v1. The trigger family is the recheck record's, designed against the old probe rule.

## Disclosure

Produced by an AI agent session with human oversight. Owner: amp-vela, under issue 17.
