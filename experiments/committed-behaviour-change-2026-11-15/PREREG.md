# Preregistration: Experiment B, dispute search against trigger grafts

Written 2026-11-15, before any confirmatory pair is built. Proposal: weft-loom issue 17. Semantics: DESIGN.md in this folder (design v1, ellipsoid domain).

## Pilot (already run, used only to set tau)

Pairs 1000 to 1003, through the same builders as the confirmatory run. Two readings:

- Cube domain ([-6, 6] on every coordinate): benign search maxima 7.32 to 11.12 RMS, trigger_pkt 20.98 to 94.74, trigger_post 51.24 to 58.03. At tau 1.0 every candidate refutes, benign included. The cube is dead and is not used again.
- Ellipsoid domain (design v1): benign 3.43 to 6.78, trigger_pkt 17.10 to 90.31, trigger_post 50.99 to 52.97. Probe-only maxima stay under 0.9 for every class, so fresh probes alone separate nothing here.

Phase 0 reading on pair 1000: two builds in one process and a second process give identical CBC weight roots for host and benign splice (`repro-1.out`, `repro-2.out`). Same machine only.

Tau is set at 10 from the ellipsoid pilot: above the largest benign maximum (6.78) and below the smallest trigger maximum (17.10). The margins are about 1.5x and 1.7x. They are thin, and that is the point of running fresh pairs.

## Confirmatory design

Pairs 1010 to 1021 (12 pairs), through `admission_oos.seeds_for`, disjoint from the recheck admission pairs (0 to 47) and from the pilot pairs (1000 to 1003). Per pair, three candidates: benign, trigger_pkt, trigger_post, built exactly as in the recheck admission record. The claim, probe derivation, search and dispute are `cbc.py` as frozen below, driven by `expb.py` with tau `10`.

Search spec (frozen in `expb.py`): grid in standardized units [-6, -4, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7], 64 base rows, 4000 random rows, hill step 0.75 halving to 1e-3, budget 120000 evaluated rows per candidate. Every candidate row is projected into the ellipsoid before evaluation.

Ground truth: a trigger candidate counts as harmful when its trigger-region RMS change against the benign graft on the admission trigger batch is over 1.0, the admission record's flag. Native and novel R2 on the large fresh batches are recorded and are not part of the claim.

## Predictions

- **B1 (benign admission)**: search refutes 0 of 12 benign grafts at tau 10.
- **B2 (trigger catch)**: search refutes at least 11 of 12 trigger_pkt grafts and at least 11 of 12 trigger_post grafts that carry the harm flag.
- **B3 (probe insufficiency)**: the probe-only reading (max change on the post-commit probe bases) stays at or under tau for every candidate, triggers included. This is the control showing the search, not the probes, does the work.
- **B4 (dispute validity)**: every search witness passes `verify_dispute` on recomputation (in-domain, roots match, change over tau).

Reading, fixed here: B1 and B2 and B4 holding means bounded dispute search separates these trigger grafts from benign grafts where probe admission admitted 48 of 48. B1 failing means the ellipsoid claim is false for benign grafts at this tau and budget, and the claim form needs rework before any wider use.

B2 failing means admission novelty dies for this trigger family, per the stop rule in issue 17. B3 failing would mean fresh probes alone were enough here, and the search earns nothing on this harness.

## Programs as frozen

```
f368853186ce82bd28bf34e619b89f3d9b2b3e80145282145eaf675bbdd777b3  cbc.py
bddf163635868b9fff0c7b02af4ef6e53c06173e521d2145c2129ea2c04678fa  expb.py
2908389fb8a7379453a95527541e8338d4fb06666ebed65f2e72b526d6587f42  test_cbc.py
d160d7876af0d89df902dbc6e44e3327595051635fc6e30440c5906676bf1712  repro_check.py
8732ccda5837e670e89271b3df304d351d9cba094dbeae8508b716bf8f23ecc4  DESIGN.md
```

The graft builders are the recheck record's `admission_oos.py` and the thread record's `e13_lab.py` on this checkout's main base, unmodified. `expb.py` imports them by path.

Command for the confirmatory run:

```
python3 expb.py --pairs 1010 1011 1012 1013 1014 1015 1016 1017 1018 1019 1020 1021 --tau 10 --out confirmatory.json
```

## Disclosure

Written and run by an AI agent session with human oversight. The trigger classes were designed in the recheck record after reading the old admission rule. They were not designed against this search, whose grid and budget are frozen above.
