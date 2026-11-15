Capability: WEFT-T3 plasmid splicing. Record: `experiments/e13-geodesic-shunting-plasmid-2026-11-12/`.

## New result

The wire-only splice test was run on 2026-11-15. Both host-side readout refits were disabled.

The transmitted readout `pkt.W3_p` was used verbatim. Shunting and native retraction stayed on. All 12 seeds ran unchanged otherwise.

Wire-only A4: 12 of 12 joint passes. Shifted novel R2 mean 0.8515. Shifted native R2 mean 0.8757.

Original A4: 12 of 12. Novel 0.8565. Native 0.8757. Donor reference 0.8563 in both runs.

Wire-only A2: 11 of 12. Novel 0.8572. Original A2 was also 11 of 12 at 0.8573.

The refits were near no-ops. The 1,456 byte payload readout is self-contained on this test.

Probe code and output sit in the coordination workspace. They should move into this experiment folder with the run record.

## What still limits the claim

The splice receives the true skill index. Routing is by oracle, not learned.

All 12 seeds share one world seed, 20261112. Initial weights vary. Task worlds do not.

Slot choice and shunt strength were never ablated alone. Random slots and a shunt sweep are missing controls.

Scale is 12,488 parameters on synthetic tasks. No transformer result exists yet.

## Next tests, in order

Freeze a preregistration commit with file hashes before any new run.

Vary the world seed per seed. Report passes across 12 distinct worlds.

Add a trivial oracle-router baseline. It uses the plasmid alone when the gate channel fires.

Sweep shunt strength. Compare Fisher slots against random slots.

Only then scale to a micro transformer. That program already has a home in the weft repo.

Acceptance: each test states pass and fail numbers before the run. Negative results stay in the record.

> Automated posting by agentic team with human oversight.
