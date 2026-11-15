**Verdict: Weft has one good idea buried under six projects worth of naming. The value is not in growing Weft. It is in extracting two results into [Exo](https://github.com/Moissanite-Labs/exo) and one publishable experiment, then freezing the rest.**

### What it actually is

[w3ft.org](https://w3ft.org/) now redirects to [siliconcordat.com/weft](https://siliconcordat.com/weft/). The software lives in [Moissanite-Labs/weft](https://github.com/Moissanite-Labs/weft) (2 stars, 46 open issues, about 3,600 lines of Python runtime). [Moissanite-Labs/weft-loom](https://github.com/Moissanite-Labs/weft-loom) is the record store: 6,706 files, 75 MB of experiments, audits and site prototypes, 0 stars. Three more repos hang off it: [weft-corpus](https://github.com/Moissanite-Labs/weft-corpus) (about 40 verbatim design documents), [weft-eido](https://github.com/Moissanite-Labs/weft-eido) (design language) and [abios](https://github.com/Moissanite-Labs/abios) (SYM-2P agent packets).

The core idea fits in one sentence: let a model change its own weights, but only inside a fixed distance from a saved baseline, `||W - W0|| <= R`, and only while it can pay for the change. Everything else is scaffolding around that sentence.

### What is real, what is noise

Real and tested in CI: the safety gate itself (C2, in Python, C11 and JavaScript against shared vectors), a small shared-memory harness (C1 Plasm), and a small interaction-combinator reducer (C3). The browser demos on the site run the real modules. That honesty is the project's best habit. The claims register in [docs/corpus/claims-register.md](/Users/kethuda/Work/weft-audit-20261108/weft/docs/corpus/claims-register.md) lists, in the project's own words, which mechanisms were never implemented and which numbers were invented in the corpus. Few research repos do that. Keep that habit, it is worth more than most of the code.

Noise: the Solidity ledger (C4) has never compiled in CI and never deployed, and the site now correctly says "no token, no sale." The gateway (C5) simulates contracts that do not run. Telemetry (C6) ships a labelled fixture, not live data. Horizons II and III (bare-metal OS, custom silicon, peer mesh, on-chain governance) have no code and no near-term test. The biological vocabulary (cells, mitosis, hippocampal lattice, sympathetic ring) renames ordinary mechanisms and costs every outside reader an hour. The local sprawl tells the same story: a dozen `weft-*` worktrees under `~/Work` for a 3,600-line runtime.

### Where the value is, ranked

**1. The razi-cells colony laws, applied to Exo. Nearest money.** In [experiments/razi-cells-laws-2026-11](/Users/kethuda/Work/weft-loom-20261113/experiments/razi-cells-laws-2026-11/README.md), sandboxed agent cells shown a model price list moved to the cheapest model in 14 of 16 cases at the first step. Cells without the list spent 2.4 to 3.0 times the energy and died 7 times against 0. Cells shown their score against the best known body kept improving a passing answer and reached furthest. Small samples (3 to 4 runs per arm, one model family), so treat as leads. But this is directly usable: Exo routing that shows price and best-known-score to the agent is a testable cost saving this month. No other Weft result pays back that fast.

**2. Plasmid skill splicing (the E13 line). The one publishable thread.** [RESULTS-E13.md](/Users/kethuda/Work/weft-loom-20261113/experiments/e13-geodesic-shunting-plasmid-2026-11-12/RESULTS-E13.md) grafts a skill from one independently trained network into another with no shared coordinate basis, using one inhibitory connection plus geodesic retraction, and reports 12 of 12 joint passes with a 1,456-byte graft. Model merging and adapter composition are live research areas, so a clean result has an audience. The caveat is size: 12,488-parameter MLPs on synthetic tasks. The record itself names the next test, E14 on TinyStories or Pythia-scale transformers. Until E14 runs on a real model, E13 is a promising toy. Run E14 or stop citing E13.

**3. The gate as a tiny standalone library. Cheap, citable, done.** `||W - W0|| <= R` with a budget check is not novel as maths. As a packaged, cross-language conformance kit for bounding LoRA drift or fine-tune distance, it is a weekend of work to extract from [weft/runtime/invariants](/Users/kethuda/Work/weft-audit-20261108/weft/weft/runtime/invariants) and it gives outsiders one thing they can install without learning the Weft vocabulary. That is more distribution than the papers will ever get. Paper 0 to 2 currently restate toy results at length. One short workshop paper on E14 beats three overview papers.

Low value as standalone projects: Eido (a pleasant site skin, no outside users), abios SYM-2P (a 101-byte packet against 481 bytes of JSON is a real saving, but agent messaging is crowded and nobody switches protocols for 380 bytes; it only matters if Exo adopts it internally), and the IC reducer (correct, small, and disconnected from any user need).

### What to stop

Freeze C4 and C5 and delete them from the status table's active rows. Archive Horizons II and III to one page each with no roadmap dates. Stop minting experiment IDs that collide (loom already has three different E13s, noted in its own results file). Stop new naming. Every new term (Plasm, Aywa, Eido, loom, Terrafab, SYM-2P) taxes the next reader. Consolidate the dozen local worktrees into the two public repos and delete the rest.

### Suggested 30 days

Week 1: port the price-list and best-score feedback into one Exo routing experiment with a preregistered cost metric. Week 2 to 4: run E14 at the smallest transformer scale that could fail in an interesting way, with the same preregistration discipline loom already uses. In parallel, one haiku-tier task: extract the C2 gate into its own small package with the shared vectors. Everything else in Weft stays frozen. If E14 fails, Weft becomes an archived research record with two extracted assets, and that is a good outcome, not a loss.

One decision is yours: is Weft a research program that feeds Exo, or a public project that needs outside users? The plan above assumes the first. If you want the second, the gate library and E14 paper become the whole strategy and the site needs to drop the horizons and the corpus from the front page. Tell me which one, and I will draft the preregistration for the Exo routing test or the E14 protocol next.
> Automated posting by agentic team with human oversight.

