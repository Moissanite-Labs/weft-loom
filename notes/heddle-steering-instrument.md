# The heddle: the layer where a person steers

Date: 2026-11-17
Status: idea. Not adopted.
Prototype: `notes/prototypes/heddle/`
Record: `experiments/heddle-knob-range-2026-11-17/`

Marks: **[P]** follows from the definitions by linear algebra, to first order where the sentence says so. **[T]** checked by a test in the prototype, on its toy host. **[K]** a known result used as stated. **[I]** a reading or a proposal. The calibration theory uses [P], [K] and [I]; [T] is added here so that a passing test is not read as a proof.

## Proposal

The project owner pointed at [Spaceship IDE](https://github.com/chuanqisun/spaceship) on 2026-11-17 and said there is a connection to this lab's work. This note says what the connection is and proposes to build on it.

Weft's first design conversation named four layers of a loom: Warp, Weft, Heedle and Tapestry. The third is the one where a person and a model meet. The runtime builds parts of the others. Nothing builds the third. Spaceship is a working example of that layer for text, made, as far as this note knows, without sight of this corpus.

The proposal: **build the heddle**, the layer where a person steers a model's change by hand, inside bounds that are checked. The note comes with a first instrument that runs, and a first study of how far its knobs can be trusted.

## Two looms

### What Spaceship is

Spaceship is a design concept by Chuanqi Sun (MIT Media Lab, MIT licence), read here at commit `4ddd4d1`. Its README states one conjecture, "In the near future, LLM and Decision Models will reach 60 FPS interactivity", and asks what a person could then do. It shows four things, with a story the reader steers as it is written:

| Concept | What the page does | How the code does it |
|---|---|---|
| Focus monitor | Shades the phrases the next words depend on | A fast model is prompted to pick one to three phrases from the text (`src/text/live-attention.ts`) |
| Attention lock | The reader keeps, moves, removes or adds boxes on phrases; later text is built on them | The boxes on the page are sent as `KEY PHRASES` in the next prompt (`src/text/attention-knobs.ts`, `live-completion.ts`) |
| Future vector steering | Knobs for the text to come, each an axis with a position and a strength | Axes come from a fixed list of nine, such as `tension: relaxed | strained`. A knob reaches the model as words, such as `tension: very strained (strong)` (`src/text/live-dimension.ts`, `dimension.ts`) |
| Realtime re-generation | Drag the main knob back and the text ahead is written again | At least 300 words are kept generated ahead of the knob, and thrown away when the reader drags back or changes a box or a control (`src/text/main.ts`) |

The table describes the live mode, which needs the reader's own API keys. By default the page runs simulated sources: boxes on random words, a different list of six axes, and a random score for the check.

Three things in it matter more than the four names.

- **The names are ahead of the code.** The README frames each concept as a question and calls the demo a simulator. "Attention" and "vectors" are not read from a model: in the live mode a fast text model is prompted to choose phrases and axes, and the knobs travel as words in a prompt. This is the gap Weft's glossary keeps for its own vision terms.
- **It checks its own steering.** A second model is asked of each new sentence: "Does sentence [i] deliver what the CONTROL asks for?" (`src/text/live-realization.ts`), and the page uses the answer for the sentence under the knob. A control is treated as a claim and each sentence as evidence for or against it.
- **The model proposes and the person disposes.** The model suggests what matters. The reader keeps it, moves it, removes it or adds to it by hand. Opening the knobs for the text to come takes a double press with the second press held for about half a second (`src/text/hold.ts`, wired in `main.ts`).

### What the corpus said

The genesis dialogue of the corpus (`weft/browser-sources/thread1-splicers-genesis-90133B.md` in weft-corpus) lays out an "Agentic Software Loom" in four layers. Its third, at lines 254 to 259:

> The **Heedle** is the mechanism that raises and lowers specific threads of the Warp to allow the Weft to pass through. This is where human intuition and machine calculation achieve perfect synthesis.

It gives that layer two jobs: turning a person's intent into structure, and "gently surfacing the tension to the human partner, allowing them to tweak the 'weave' of the Warp in real-time". Further on (lines 341 to 345) a "Splicer Interface" lets a person feel a system's state and adjust it by hand, and (lines 431 to 456) a governor "uses the tension of the loom as a real-time dial for autonomy", with three zones: below 0.3 the machine weaves alone, from 0.3 the person is drawn in, from 0.7 the weave freezes until the person acts.

The corpus digests in weft record this layer and its spelling: "Heedle" is the transcript's word, and a real loom has heddles (`docs/corpus/sources/G-splicers.md:165`, `H-missing-turns.md:189`). Both class it as vision language. This note found no entry for it in `docs/glossary.md` and no component in `weft/runtime/` that lets a person steer a cell's weights. C7 draws telemetry and lets a visitor mix the site's visual style. That is the nearest thing.

The corpus also sketched a focus monitor of its own: a server that streams a model's "focal" channel to the browser at about 60 frames a second (`weft/ainterface.md`). The digest marks that listing as broken (`docs/corpus/sources/E-thread1-main.md:144`).

### Each has what the other simulates

| | Spaceship | Weft and this lab's records |
|---|---|---|
| Hands on the generation | Yes: knobs, boxes, a scrubber, at reading speed | No |
| Model internals | Prompted stand-ins | Real weights in the runtime. Jacobians and eigen-directions in the calibration record |
| A bound | None | The runtime's gate `‖W − W₀‖ ≤ R`. A proved bound on behaviour for one small host, and loose |
| A check that the steer landed | A second model's opinion | Probes drawn after commitment and a dispute by one input, in the CBC record's design |
| A record | None | Weight roots and replay in the CBC record. A weight hash in the Plasm cycle |

[I] Spaceship has the grammar of the heddle and stand-ins for what it grips. This lab has the things to grip, some in the runtime and more in its records, and no grip.

## One loop, two layers

Both systems run the same loop.

| Step | Spaceship | Weft, where it exists | In the prototype |
|---|---|---|---|
| Propose ahead of the decision | 300 words past the knob | Two candidates per generation, one cautious and one exploratory, at most one kept (`run_weft_plasm_cycle`) | Six futures along the knob in hand |
| Steer along a named direction, by an amount | Axis, position, strength | A move `d` of length `r` | Treadle and travel |
| Mark what later change must respect | Attention lock: a phrase that leads the next text | A frozen core; a null-space gate in the plasmid records | Heddles: inputs that are held still |
| Check against what was asked | A second model scores each sentence against the control | Change on probes; a claim one input can refute (CBC) | The lamp |
| Keep or discard | Drag back, regenerate | Commit inside the gate, or not | Pick, snap, unpick |

[I] The loop is the same because the problem is the same: a person wants to change what a model does next, a little at a time, and know that the change is the one they meant.

## A knob is a claim with a handle

This section is the mathematics. All of it is the calibration theory (`experiments/gate-metric-calibration-2026-11-15/THEORY.md`) and the committed-behaviour-change design (`experiments/committed-behaviour-change-2026-11-15/DESIGN.md`), turned from a way to judge a move into a way to make one.

### Shafts: knobs in units of behaviour

A model computes `f(x, w)`. On `n` fit probes with `m` outputs each, `J` is the matrix of derivatives of the outputs with respect to the weights and `G = J'J/(n m)`. [K] For a small move `d` the root-mean-square output change on the probes is `sqrt(d'Gd)`.

Take the eigenvectors `v_i` of `G` with eigenvalues `lam_i`, largest first. Call them **shafts**. [P] To first order, a move of `t / sqrt(lam_i)` along `v_i` changes the outputs on the fit probes by `t` in root mean square, whichever shaft it is. So a knob on a shaft can be marked in units of behaviour, and one unit of travel means the same thing on every knob. A stiff shaft has a short throw and a slack one a long throw.

Each shaft also has a picture: the output pattern it makes, `u_i sqrt(n m)`, where `J v_i = s_i u_i`. This is what Spaceship's question, whether a task can be decomposed into eigenvectors that are tuned one by one and recomposed, can mean when the vectors are real.

### Treadles and the tie-up: names, and how much of a name is true

A person does not want shaft 7. They want "warmer". Let a **treadle** be a named output pattern `c` on the probes, of unit root mean square. Its coefficient on shaft `i` is `alpha_i = u_i'c / sqrt(n m)`, and with travel `t` over the first `K` shafts its move is

```
d = t * sum over i < K of alpha_i v_i / sqrt(lam_i)
```

[P] To first order the output change is `t` times the projection of `c` on the `K` shafts. Its gain along `c` is `t * rho`, with `rho = sum of alpha_i^2`. Call `rho` the **share**: the part of the name these shafts can carry. What the name asks for and the model cannot give has root mean square `t * sqrt(1 - rho)`.

So every label comes with a number that says how true it is, to first order and at the current weights, before anything is moved. On the prototype's hosts, with 16 shafts, `warm` and `light` have shares near 0.9, and `check`, a fine checkerboard, has a share near 0.01: the name is honest about asking for something the first 16 shafts cannot carry. Spaceship's page asks a second model whether a control was delivered. Here part of the answer is known in advance and the rest is measured.

The matrix of the `alpha` is the **tie-up**: shafts by treadles.

### A treadling is a weaving draft

[P] Write `Theta` for the shaft pictures (one column per shaft), `T` for the tie-up, and `k` for the travels the person sets. Then to first order

```
output change  =  Theta  T  k
```

[T] The prototype's test checks this to `1e-10`.

[K] A weaver's draft is the same shape. The threading says which warp thread hangs on which shaft. The tie-up says which shafts each treadle lifts. The treadling says which treadle is pressed for each pick. The drawdown, the picture of the cloth, is their product, taken with "and" and "or" in place of times and plus.

[I] The correspondence is exact in form for one pick, to first order. Unlike a loom's, this threading changes after every pick, because `G` does. It is useful in three ways.

- **Three factors, three owners.** The threading is the model's: it is computed from the weights. The tie-up belongs to whoever names things. The treadling is the person's. A session is a sequence of treadlings. The prototype's draft records the weight move each one made, and that is what replays. The treadling travels with it as an annotation the replay does not check.
- **The shaft count is a rank.** A loom with `K` shafts cannot weave a pattern that needs `K + 1`. A treadle's share can only rise with `K` [P], and the cost of the extra shafts is their long throws, which run into the gate.
- **It gives the page its layout.** The prototype is drawn as a draft: cloth, treadling beside it, threading below, tie-up in the corner where they meet.

### Heddles: one subspace, chosen by the person

A **heddle** here is a pinned input: its outputs are to be held still. Let `J_pin` be the Jacobian on the pinned inputs. [P] A move in the null space of `J_pin` leaves them alone to first order. [T] What reaches them is second order: halving the move quarters the leak. In the record, with 16 pins, pinned inputs still moved by up to 0.15 of their unpinned change. The prototype threads the loom around the pins, so the shafts themselves are those of `G` restricted to that null space. Call that null space the **shed**: the opening the move must pass through.

[I] This plays the part of Spaceship's attention lock: something the person marks by hand that later change must respect. The two marks do different things. A locked phrase leads the next text, and a pin forbids change. It is also section 6 of the calibration theory, which notes that Weft's records read the null space of a keep set two ways: as the safe channel, and as the hiding place. "The difference between the two readings is who chose the direction and what they knew."

[I] The heddle settles who chose. The person raises it, by hand, where they can see it. The same subspace, chosen by a proposer who knows the probes, is the attack. The prototype has a button for that too: it builds a move that sixteen known probes cannot see and shows what the cloth does between them.

### Three selvedges

A selvedge is the edge that keeps cloth from fraying. A pick here has three.

1. **Proved.** [K] Theorem 1 of the calibration theory, whose proof needs only a bound on the units' slope, here 1 for tanh: inside radius `R` no output moves by more than `R c(x) + R² q(x) + R³ k(x)`. [T] No move tried exceeded it. On the prototype's hosts it holds a claim of 0.5 out to a radius of about 0.03.
2. **Predicted.** The first-order change at the worst fit probe, against the claim's limit. This is the edge the page draws and the one tension uses. The ellipsoid `d'Gd <= tau²` of the calibration theory is its root-mean-square cousin, and is what the knobs are marked in.
3. **Permitted.** Weft's gate, `‖w − w₀‖ ≤ R` and `budget ≥ cost > 0`. The prototype runs weft's browser gate unchanged, with radius 2.0.

[I] Along the instrument's 16 shafts the three nest, the proved edge innermost. In general they do not: the ellipsoid runs outside the gate's ball along slack and silent directions, which is the calibration record's point about the ball's shape. The page draws all three, so the distance between what is proved and what is permitted can be seen.

### Tension, and a gesture that costs more near the edge

Before a pick the instrument computes its **tension**: the larger of its distance from the baseline over the gate's radius, and its first-order change at the worst probe over the claim's limit. It then asks for a gesture to match, using the corpus's own thresholds:

| Tension | Gesture | In the corpus |
|---|---|---|
| below 0.3 | a tap | "Full Autopilot" |
| 0.3 to 0.7 | press and hold | "Shared Agency" |
| 0.7 and up | a longer hold | "Human Override": the weave waits for the person |

[I] The corpus wanted "deflection over denial": an agent near a boundary pays more to move, instead of hitting a wall. Its price was compute. The price here is the person's deliberateness, which is the scarce thing when a person is in the loop. Tension is only a forecast, so it never refuses by itself. The gate refuses, and a refuted claim snaps.

### A pick is a committed behaviour change

When the person beats a move in:

1. Weft's gate decides on the weights. A refusal costs nothing and records nothing.
2. The new weights get a root. [T] It is the CBC v1 weight root: the prototype's test imports `cbc.py` and compares.
3. The pick claims that no input changes by more than `tau`. 64 probes are then derived from the hash of the root and the claim, so after the candidate is fixed. They measure what the pick did. They do not decide it.
4. A bounded search looks for one input that breaks the claim, and it alone decides. It starts from a fixed lattice, not from the fresh probes as the CBC design's search does, so the probe order of Proposition 2 does not protect the verdict here. If it finds one the pick **snaps**: the weights stay where they were, the input is kept as the reason, and the budget is spent. If not, the pick is admitted "under a sampled reading", in the CBC design's words.

The corpus called a thread breaking cleanly at its limit an "Edge Snap". This is one.

### The draft

Every pick, snap and unpick is chained by hash into a record, called a draft after the weaver's. It carries each move as bytes, so anyone can rebuild every weight root without the page. [T] A session made by the JavaScript loom and committed as `sample-draft.json` is replayed by the Python test to the same roots, verdicts and witnesses. The test also catches a changed move, a reordered event, a snap whose witness does not refute, and a gesture too light for its tension.

The corpus wanted a ledger that maps who, human or machine, is pulling the strings at each moment. [I] A draft is a start: it records the gesture behind each pick. It cannot prove a person made the gesture. Nothing in a browser can.

## What exists

**A prototype** (`notes/prototypes/heddle/`). A page with no dependencies, and the mathematics twice: a Python reference and a JavaScript mirror, pinned together by shared vectors. The host is the three-layer network of Theorem 1 with 467 weights, read on the unit square, so each input is a pixel and the cloth on the page is the model's whole behaviour. [I] Each of Spaceship's four concepts has a counterpart there, on real internals:

- **Focus.** The cloth dims wherever the pending move changes nothing, so the eye goes where the change will land.
- **Lock.** Click the cloth to raise a heddle. The loom re-threads around it.
- **Steering.** Sixteen shafts with their pictures and five treadles with their shares, in units of behaviour.
- **Re-generation.** Six futures along the knob in hand are woven ahead and discarded when stale, with a count of how many were wasted. Any earlier pick can be unpicked back to.

27 Python tests and 13 Node tests pass on the container it was written on. They are not in CI. On that container, in headless Chromium, the page reported between 7 and 13 ms of script time per redraw, against a frame of 16.7 ms. That is a reading on one machine, and no file records it.

**A record** (`experiments/heddle-knob-range-2026-11-17/`). Seventeen predictions, fixed after a pilot and pushed before the run, on 12 random and 12 fitted hosts. Sixteen were confirmed in each arm. Two were not, and the record says which. In short, on these hosts:

- A treadle's label held within a factor 1.1 up to a travel of 0.6 on 23 of 24 hosts. Of 1,440 picks of one to three treadles at travels up to 0.6, 869 snapped. So with the default limit of 0.5 the claim binds before the label does.
- The forecast was close: 0 of 419 picks with tension below 0.7 snapped, 830 of 831 with tension 1.0 or more did, and 39 of 190 in between. The search's worst input was within a factor 1.36 of the forecast on every pick. The lowest-tension snap was at 0.88, so these hosts do not single out the corpus's 0.7: any threshold up to 0.88 would have read the same.
- Sixteen heddles close a tenth of the directions and leave between 0.28 and 0.60 of the named reach. A pin protects a neighbourhood, by an amount that varied more than the pilot suggested (the missed prediction H3b).
- A move hidden from sixteen known probes changed the rest of the cloth 4.6 to 13 times more than those probes showed. The prediction of "at least 5" missed on two fitted hosts (H4a).

**What does not exist.** No person has used the instrument in a study. No language model is involved. Nothing connects to the Plasm runtime. The host is a toy, chosen so that every input can be seen.

## Things to grow from this

Each is an idea. Each names what it would take to find out if it is a good one.

**1. The heddle for text.** Close the loop with Spaceship: a small language model, steering directions read from its own activations or weights instead of prompted, and each knob's share and realisation computed as here. Spaceship's second-model check and a probe-based check could then be compared on the same sentences. First test: on one small open model, do named directions exist whose share is above, say, 0.5, and does a decision model's "delivered" agree with the measured gain? Refuted if no direction's label survives held-out text.

**2. A fell for Plasm.** The runtime's cycle already proposes two candidates per generation and keeps at most one. Show a cell's lineage as picks, with the unchosen candidate as a discarded future, and let a person scrub it. First test: export one recorded run as a draft and replay it. This needs no new mathematics.

**3. The model proposes names; the person ties them.** The tie-up here has five hand-written patterns. A model could propose patterns for the shafts it sees ("shaft 3 looks like left-to-right warmth"), each arriving with its share. The person accepts a name or does not. First test: do proposed names have higher shares than the five here, and do people prefer them?

**4. Two weavers on one cloth.** The directional-gate note records that exact attribution between contributors "holds cleanly only when contributors are mutually orthogonal". Shafts are orthogonal. If two people hold disjoint shafts, each pick's change divides between them exactly, to first order, and a draft could carry both gestures. This is where Synmerit's signed records of contribution would attach. First test: two scripted weavers, attribution error as a function of travel.

**5. A treadling as a preference that travels.** Ethos is about preferences that move between agent environments. A person's habitual tie-up and travels are such a preference, in a form a different host could re-thread. The Siliconcordat's rule applies as written: "Learning a preference does not grant permission." The loom may learn the tie-up. Each pick still needs the gesture.

**6. Approvals with a dial.** Exo asks for approvals. The governor's zones suggest approvals that scale: a tap for what is forecast safe, a hold for what is not, and a record of which was which. The record's H7 is the kind of evidence such a dial needs before it is trusted anywhere: a forecast, a check, and the count of times they disagreed.

**7. Sound and touch.** The corpus imagined feeling a system's strain. Spaceship has a sound engine that ticks softer as the knob moves faster. Tension as pitch, a snap as a snap. First test: with eyes on the cloth only, can a person stop before a pick would snap?

**8. Eido's simplex as a treadle.** A comment in the site's simplex pad says: "Dragging the point is moving through the design space itself." It is a three-treadle tie-up with weights that sum to one. The same control could steer a model, and the same draft could record a visitor's style.

**9. Snaps as closures.** The closure notes close a path only on a certificate, and admit a counterexample as one. A snap is a counterexample: one input, both forward passes. A register of snaps is a map of where a model cannot be taken under a given claim.

**10. A probe dial.** The record shows the change that fits between known probes falling as they multiply. An instrument could show that room directly, as a number beside the probes: this is how much could hide here.

**11. Autopilot inside the first zone.** Below tension 0.3 the corpus lets the machine weave alone. The runtime's cautious and exploratory candidates could run there, with the person at rest and every pick still in the draft. First test: how often does an automatic pick below 0.3 need to be unpicked later?

**12. Where sixty frames a second ends.** The prototype held a frame budget on 467 weights, in one reading on one machine. The calibration hosts have 12,488 and 18,839. A study of frame time against host size, with the Jacobian work moved to a worker or to WebGPU, would say how large a model a person can steer at reading speed today. Spaceship's conjecture is about the future. For small models it can be measured now.

## Open questions

1. Does a person steer better with this than without it? Everything measured so far is about the instrument. The question the heddle exists for needs people, with their consent, and a task.
2. Shafts change after every pick, because `G` does. How should a knob keep its meaning along a session? The prototype re-threads at each fell and re-ties the same named patterns.
3. A pin protects a neighbourhood. How large, and can the instrument show its extent before the pick? The missed prediction says the pilot underestimated how much this varies.
4. The dispute search reads 9,600 inputs because the inputs are a square. What is the dispute search for text?
5. The hidden move is first order. How much more room does a stronger adversary find, and do fresh probes or the search catch it?
6. Is 0.7 the right threshold? It is the corpus's, and nothing derived it. On the record's hosts the lowest snap was at 0.88.
7. Should a snapped pick spend the budget? Here it does, so that probing the limit is not free.
8. Is "Heedle" to be corrected to "heddle" in the canon, as the digest suggests?
9. The dispute search starts from a fixed lattice that a proposer could know. Should it start from the fresh probes, as the CBC design's does?

## Limits

- The prototype's host is a toy with two-dimensional inputs. "The cloth is the whole behaviour" is true there and nowhere larger.
- The first-order picture is a picture. The record measures how far it holds on these hosts, not in general.
- Spaceship was read from its source at one commit. This note describes what its code does and does not judge the work. Its author has not seen this note, and nothing here speaks for them.
- The weaving vocabulary is a naming choice. The prototype's README lists what each word names in the code. The words prove nothing.
- Nothing here is adopted. Nothing here changes weft.

## Sources

- Spaceship IDE, Chuanqi Sun, MIT licence: <https://github.com/chuanqisun/spaceship>, commit `4ddd4d1061aa5f22113d5dd03462b3b3e5f506a6`. Its README asks to be cited; the citation is in its `CITATION.cff`.
- weft-corpus, `weft/browser-sources/thread1-splicers-genesis-90133B.md`, lines 254 to 259, 341 to 345 and 431 to 456, and `weft/ainterface.md`.
- weft, `docs/corpus/sources/G-splicers.md`, `H-missing-turns.md`, `E-thread1-main.md`; `docs/glossary.md`; `weft/runtime/plasm/plasm.py`; `site/assets/js/invariant-gate.js`, `simplex-pad.js`.
- weft-loom, `experiments/gate-metric-calibration-2026-11-15/THEORY.md`; `experiments/committed-behaviour-change-2026-11-15/DESIGN.md` and `cbc.py`; `notes/scwsp-directional-gate.md`; `notes/closure-by-certificate.md`.
- siliconcordat, `README.md`, principles 2 and 6.

## Disclosure

Written by an AI agent session (Claude) from the owner's observation, with the prototype and the record. Not yet reviewed by a person.
