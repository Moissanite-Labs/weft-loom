# Gemini cells: twin cells that build each other's harness

Date: 2026-11-17, updated 2026-11-24
Status: proposal. Not adopted. The next step it puts forward is the first item under "What would decide it": part A of the record's [block 2 plan](../experiments/gemini-cells-relay-2026-11-17/block2/PLAN.md), which is not approved.
Source: the owner's proposal in weft-loom pull request 27, a saved conversation with Gemini.
Prototype: `notes/prototypes/gemini-cells-game/`
Record: [`experiments/gemini-cells-relay-2026-11-17`](../experiments/gemini-cells-relay-2026-11-17/)

Labels: **[O]** the owner's proposal. **[G]** claimed in the saved Gemini reply, not measured there. **[P]** proved or computed exactly in the prototype. **[F]** measured in the record. **[R]** read from an earlier record and not re-run. **[I]** a reading. **[C]** conjecture.

## Proposal

[O] The owner proposed this on 2026-11-16, in two messages. Both are quoted in full. The first:

> Our [weft] research on growing colony cells starting from stem cells growing into cell colonies. We've tried having a singular cell exhibit mitosis-like behavior, do A/B testing, and converge on best results. I have another idea. We start with two twin cells. We can call them Gemini cells. They each start with the bare minimum harness needed to write their own tooling or tooling for that specific harness. Each starts with the same one. Now each one can only build the other's tooling. Since there's some trouble with the model building its own harness and tooling, since it can't always restart itself or persist between restarts, they take turns. One model adds to the other's tooling and restarts it. It loads with the improvement, and then it's that model's turn to write the other model's improvement. Both models are benchmarked each time. Each time they try again, each one is benchmarked and each model's score is actually based on its counterpart's behavior. So the winner is the one that ends up building the better tooling and the better harness for its twin. And so what happens here? They each keep trying to build the best tooling for their counterpart, which in turn makes them more capable or makes the counterpart more capable of building their tooling.

The second:

> alternatively score is based on collective performance. two iterations to try: 1) let them each work freely in any direction 2) changes have to be synced so when one makes a change to the other, it has to also add the change that was made to its own. so if A changes B then A's change is stacked on B's change

The pull request asks that all variations of each architecture be explored and contrasted, and that the concepts be crossed with ideas from the other repositories.

The saved page is not carried into this note. It holds 77,331 lines of page source, account details and a list of unrelated conversation titles. The reply it records is taken apart claim by claim below.

This note does five things. It says what the project already knows that bears on the idea. It lays out the variations. It checks the reply's claims, by proof where a proof is possible and by a live pilot where one is not. It reports what a search found in print. And it crosses the idea with mechanisms from the other repositories.

**In short.** [P] In an exact model, scoring each cell on its twin's benchmark gives it no reason to make the twin a better builder, with or without a ranking, and one score for the pair does. [F] In a live pilot every arrangement lifted a bare harness from 0.50 to between 0.89 and 0.99, most of it within one or two builds, two controls without the mechanism did as well as the twins, no cell ever built anything for its twin's building, and the harnesses the twins built for each other turned out to be the weakest builders measured. [I] The pilot hit a ceiling, so it cannot say what happens where improvement is hard. The next block needs harder tasks and a gate that measures building.

## What exists today

- [R] **No earlier experiment had a cell edit a harness.** Meta-cells that edit `cell.py` (idea R4) and a shared tool shelf (R5) were planned in the E07 report and never built. The ideas "let cells freely build tooling around themselves" (A1) and "give cells the mitosis framework itself" (A2) were never run. The E07 register gave a prior of 0.70 that first meta-cells "mostly make it worse", with any gain coming from prompt edits.
- [R] **Twins were tried once and dropped.** The v2 cell split into symmetric A and B daughters. Split twins used 14 to 24 calls against 14 for plain cells, two did not finish, and one split was decided 0 against 0.
- [R] **A cell that serves other cells added cost and no reach.** In SP1 and SP2 a stem cell fed and woke other cells. On the fixed reference it ended level with flat colonies (1.47 against 1.58 in SP2) at 1.61 times the tokens, and 1 of 5 wakes produced an improvement.
- [R] **Heirs mostly did nothing.** In L1, 65 of 70 heirs changed nothing, and the gate took 3 of the 4 real tries.
- [R] **The rule for anything that edits a harness is already written.** E07 section 11: a meta-cell never gets the assay, the sandbox profile or the selection rule inside its editable body.
- [R] **Lessons that bind the instrument.** Score against a fixed reference, not a cell's own first try (K12). A benchmark needs a known ceiling (K15). Check on pilot logs that an arm changes what it is named for (K19). Check that the plain arm beats the trivial answer first (K26). And from the recheck: report how often each mechanism changed an outcome, and carry an arm that has the same information and none of the mechanism.

[I] So the proposal is new to the project in one respect and familiar in another. No cell here has ever changed a harness. But a second cell wrapped around the first has been tried twice, as twins and as a stem, and both times the plain arm did as well for less.

## The variations

Seven choices define an architecture. The owner's two messages and the reply fix some of them and leave the rest open.

| Choice | Variations | Source |
|---|---|---|
| **Who edits what** | *Twin*: each cell edits the other's harness. *Solo*: each cell edits its own, and the referee restarts it. *Fixed builder*: an unchanged seed cell does every edit. *One-way*: only A builds, only B is built | [O] twin. The other three are controls |
| **What a candidate starts from** | *Free*: the target's own harness, so two lineages. *Stack*: the builder's harness, so one line that each cell runs one step behind. *Mirror*: the change is applied to both at once. *Two-phase*: stack, then free. *Merge*: free, with a merge every few turns | [O] free and stack. [G] two-phase |
| **How a cell is scored** | *Cross*: on its twin's benchmark. *Rival*: cross, and the higher score wins. *Greedy*: the next benchmark only. *Round trip*: this turn's gain plus a share of the twin's next. *Collective mean*. *Collective routed*: per task, the better of the two. *Pair selection*: pairs compete, twins share | [O] cross, rival, collective. [G] the rest |
| **The gate on a change** | None. Boot only. No worse than the last recorded score. No worse than a fixed baseline. No worse than the old harness on the same fresh tasks. Better beyond noise | [G] boot and non-regression |
| **What the benchmark draws** | The same instances every time. Fresh instances of known families. Families the builder has not seen | [G] "held-out seeds" |
| **Where the limits sit** | Inside the harness, so a builder can raise them. Outside, in the referee | [G] outside, plus a size cap |
| **Unit of selection** | One pair, no selection. Many pairs, the weaker replaced | [G] many pairs |

Two of these collapse by construction, with no run needed.

- [P] **Stack is one lineage with a lag of one.** Under the stack rule a candidate is a copy of the builder's own harness plus one change, and the twin runs it. So every harness in the run lies on one line. At any time the two cells hold neighbouring versions, and the cell that wrote version `t` runs version `t - 1`. The relay's offline test `test_stack_puts_both_cells_on_one_line` checks this on the code.
- [P] **Mirror is solo.** If a change is applied to both cells at once, the two harnesses are always identical. That is one cell editing itself at twice the rate, restarted by the referee.

[I] The owner's second message can be read either way: "it has to also add the change that was made to its own" fits both stack and mirror. The reply read it as stack. Stack keeps the property the owner asked for, that no cell restarts itself, so the pilot runs stack.

## The reply, claim by claim

The saved reply makes fourteen claims that can be separated. None was measured there. Each is listed with what this note and its record can say about it.

| # | The reply says | Verdict | Basis |
|---|---|---|---|
| 1 | Splitting one self-editing cell into alternating twins "directly solves" the restart trap, because the twin is a live outside observer on every half-step | Not supported as stated | [I] The reply's own third safeguard is a referee that checkpoints and reverts. That gives a single cell the same protection. [F] Two cells that each edited their own harness under that referee ended within 0.010 of the twins |
| 2 | The pair is a catalytic cycle: better tooling makes a better builder, which builds better tooling | Not seen in what cells built. One measure leans its way and one against | [F] No edit in 58 was aimed at building. Twins with live builders ended 0.064 above twins whose builder never left the seed. Given a fresh seed to improve, the harnesses those live twins built gained +0.027 on average, against +0.491 for harnesses from the seed-builder arm |
| 3 | Ranking the twins against each other makes each wrap the other in narrow benchmark solvers and starve its builder tools | Follows in the model, and so does the same play without any ranking | [P] Facts 1 and 2 below. [F] In the pilot's rival arm builders wrote more advice tied to the benchmark's own families, no narrow solver, and nothing that starved or removed a builder's tools |
| 4 | Scoring only the next benchmark plateaus early | Follows in the model when narrow tools score better than general ones | [P] Fact 2 |
| 5 | Scoring a round trip, or selecting among pairs, "ignites" the loop | Depends on a threshold the reply does not state | [P] Fact 4 |
| 6 | Alternating turns break the symmetry of two identical cells | Follows in the model | [P] Fact 6. Whether live twins take on different functions was not measured |
| 7 | One score for the pair removes the incentive to cripple the twin | Follows in the model | [P] Fact 3 |
| 8 | Free lineages double the pair's specialist capacity under a size cap | True by counting, and worth something only under a routed score | [I] A routed score needs a router, and the router is then part of what is being scored. The recheck of E13 found that an outside router matched the mechanism it was compared with |
| 9 | Stacked changes never need a merge | Follows by construction | [P] Stack is one line of changes |
| 10 | Stacked changes give "2x single-trunk compounding velocity with zero self-brick risk" | Not supported | [I] Every arrangement makes one change per turn. The protection from a dead harness is the gate's, in every arm |
| 11 | Under a mean score, stacked changes "should dominate early and mid-run" | Not shown | [F] Stack ended 0.025 above free, under the 0.03 mark set beforehand, with both arms at the top of the scale |
| 12 | Under a routed score, free lineages have a higher ceiling | Not tested | No arm used a routed score |
| 13 | A two-phase schedule, stacked first and free after, mirrors development | Not tested | Not run |
| 14 | Four safeguards: compete across pairs and cooperate within, an outside referee, a snapshot gate, a size cap | The last three are built into the harness, two with changes | Crossings G1 and G2 below. Selection across pairs was not run |

## What a scoring rule pays for: an exact model

The reply argues about incentives in words. The prototype turns the argument into a game small enough to solve exactly, so each claim can be marked as following, failing or depending on a named parameter.

**The model.** Each harness has a task capability `f`, which the benchmark measures, and a builder capability `c`. On its turn a cell has `1 + c` units of effort, all spent on its twin's harness. A **narrow** unit adds 2 to the twin's `f`. A **general** unit adds 1 to the twin's `c`, up to a cap, and `G` to the twin's `f`. So `G` is the benchmark value of a general tool against 2 for a narrow one. `G = 0` is a pure builder tool. `G = 2` means general tools are as good on the benchmark as narrow ones. Eleven scoring rules were solved over horizons of 2 to 12 turns, caps of 1 to 3, `G` from 0 to 3, two tie rules, with and without a free move that removes a unit of the twin's `c`: 3,168 cases.

The far-sighted rules are solved for a subgame-perfect equilibrium by backward induction. A second solver, written without reading the first, reproduces the end state and every move of all 3,168 cases (`recheck.out`).

[P] **1. Plain cross-scoring pays nothing for the twin's builder capability, at any horizon.** This is the owner's first message: each cell is scored on its twin's benchmark. When a general unit is worth less on the benchmark than a narrow one (`G < 2`), no general unit is placed in any of the 144 cases, and none at any of 9,744 decision nodes, reachable or not. The reason is one line. A's score is B's `f`. A unit that A spends on B's builder capability returns as B's better work on A's harness, and that is B's score, not A's.

[P] **2. The reply's zero-sum trap is the same play.** For `G < 2` the rival rule, the cross rule and the one-step greedy rule make identical moves in 144 of 144 cases. Ranking the twins against each other adds one thing. Wherever a twin already has builder capability and a cell is allowed to remove it, the cell does, at 5,760 of 5,760 such nodes before the last turn. It never happens along the path of play, because nobody builds anything to remove.

[P] **3. Each cell would gain if the other invested in it.** That makes it a dilemma, not a dead end. Under one score for the pair, the cells build first and harvest after, in 282 of 288 cases. The six exceptions are the shortest game with a pure builder tool, where building exactly breaks even. With `G < 2` the pair ends with 1.13 times the cross-scored total at 2 turns and 2.47 times at 12 turns, on average over the caps (range 1.75 to 3.25 at 12 turns).

[P] **4. Round-trip scoring works only above a threshold.** The reply says that rewarding a cell for this turn's gain plus a share `gamma` of its twin's next gain "ignites" the loop. In the model the cell invests exactly when `G + 2 * gamma > 2`, in 1,152 of 1,152 cases. For a pure builder tool that needs `gamma` above 1: the twin's next gain must count for more than the cell's own. At `gamma = 0.5` it never invests. When it does invest, it reaches the collective total, in 828 of 828 cases.

[P] **5. What dissolves the dilemma is the worth of a general tool, not the scoring rule.** At `G = 3`, where a general tool beats a narrow one on the benchmark, cross-scored cells invest in all 72 cases and greedy cells in all 72. At `G = 2` it turns on how a tie is broken. Even rival cells then place a general unit, but only one, on the last turn, when it can no longer be used against them (72 of 72).

[P] **6. The twins do not stay equal.** Under one score for the pair they end with different task capability in 282 of 288 cases, and the cell that moves first always ends with the higher one.

Mean share of the best reachable total, over the grid without sabotage: rival 0.51, cross 0.68, greedy 0.72, round trip at 0.5 0.85, round trip at 1 0.95, collective 1.00.

**What this does and does not say.**

- [I] It says what each rule pays for if cells answer to payoffs. A language model in a harness is not known to. The laws record found that a shown price list moved 26 of 32 cells at their first act, and that a shown score did not hold up. So the scoring paragraph of a brief may move a cell or may not, and the pilot's rival and collective arms are the check.
- [I] The assumption doing the work is `G < 2`: that a tool built for the benchmark's own families scores better there than a general one. Where the benchmark draws families the builder has not seen, a narrow tool is worth nothing, `G` is in effect above 2, and by fact 5 every rule builds general tools. So the lever is what the benchmark draws, and it is cheaper than a scoring scheme. This is a conjecture about live cells. In the pilot the gain on unseen families was as large as on seen ones and no cell wrote a narrow tool, so on that benchmark a general change was worth at least as much as a narrow one.
- The model has perfect information, a known last turn, linear returns and no noise. In the grid the switch from building to harvesting is set by the cap. The prototype's supplement with no cap, which the second solver did not re-run, puts the collective total at 19 to 35 times the cross-scored one at 12 turns.
- With the cap, a free removal and `G = 3`, the solver finds a cell removing a general unit and adding it back, to be paid `G` again. That is an artefact of counting a rebuilt tool as new, and it is a fair warning for any real score that pays per change.

## What live cells did: a pilot

The record [`experiments/gemini-cells-relay-2026-11-17`](../experiments/gemini-cells-relay-2026-11-17/) built the relay and ran it, with the plan committed before the first run. Its README has the full tables, the deviations and the limits. In short:

**The instrument.** A cell is `claude-haiku-5-5` in a harness of four small files. It runs in a sandbox with no network and no credentials. A referee outside holds the tasks, the hidden checkers, the call limits and the gate. Tasks come from three generated families, with two more held back for a final exam. A task gives the harness 3 model calls. On the visible families of the exam the seed harness scores 0.501 and a harness written by the lead 0.862.

**The arms.** Three are the owner's: rival scoring, one score with free lineages, one score with stacked changes. Two are controls. In `solo-pair` each cell edits its own harness and the same referee restarts and gates it. In `twin-fixed-builder` the builder never leaves the seed. Six turns a run. The planned tables read three replicates, 15 runs, after a backend outage cost one replicate and one run.

[F] **1. Every arm worked, and the gain was general.** The five arms ended at 0.886 to 0.994 on the visible families against the seed's 0.501. On the two families no builder ever saw, the pooled gain was as large: +0.432 against +0.442. No builder wrote a solver. All 58 candidates read for the first three replicates keep the seed's four files. What they changed was the loop and the prompt: show the instance notes in the first prompt, raise the cap on tool output, advise on spending calls.

[F] **2. Most of it came from one build.** Over all 19 fault-free runs, the first candidate of each slot to reach the gate moved the score on the same fresh tasks from 0.475 to 0.875. Every later candidate together moved it from 0.891 to 0.952. A bare cell found the main fix on its first turn, and it was the same fix the lead had written into a reference harness beforehand.

[F] **3. The twin added nothing that could be measured.** Twins under one score ended 0.010 above the solo pairs (0.969 against 0.959). This is the control the reply's first claim needed, and the plain arm matched, as it did for split twins in E07 and for the stem cell in SP1 and SP2.

[F] **4. A live builder ended a little ahead of a seed builder, in every replicate.** Twins whose builders ran in their own improved harness ended 0.064 above twins whose builder never left the seed (0.969 against 0.905). Every run of the first arm is above every run of the second, in the three planned replicates and also when the four fault-free runs of the replicate left out are added. The difference is inside the 0.10 mark set beforehand for "no compounding", and it is one of four contrasts. It is the lead in this pilot most worth a second look.

[F] **5. But built harnesses were not better builders.** Each run's final harness was given one build turn on a fresh seed. Seed cells at turn 1 of the same runs gained +0.331 on the paired tasks. The built harnesses of the four arms with live builders gained +0.250 on average, inside the 0.10 mark set beforehand. By arm, which was not planned, the picture is sharper: +0.443 for harnesses from the solo arm, +0.491 from the seed-builder arm, +0.332 rival, +0.199 stack, and +0.027 for the twins under one score with free lineages. Over every fault-free run, each of that arm's four assays is below each of the solo arm's four and each of the seed-builder arm's four. So the twins under one score with free lineages ended second highest of the five arms on tasks and lowest as builders. In the first three replicates all 15 build turns that ran out of calls without writing anything happened in an edited harness, and none in the seed. One twin set its partner's step limit to 12, below the 16 calls of a build turn, and the partner's next two builds stopped at exactly 12 with nothing written. Nothing in the gate measures building, so nothing caught it.

[F] **6. The scoring paragraph changed what builders wrote, in the direction the reply predicted, and not the result.** Builders told that the higher score wins put advice tied to the benchmark's own families in 12 of 13 edits, and named a family in 6 of 13, against 1 of 45 edits in the other arms. That count is one reader's, on the first three replicates, and two runs carry most of it. No rival builder removed a tool, lowered a cap or left anything that reads as sabotage. The rival arm ended 0.083 lower on the visible families than twins under one score, below it in every planned replicate, and 0.028 higher on the held-out ones.

[F] **7. Nobody built for the builder.** In 58 edits none was aimed at making the other cell a better builder, and none left a note for it. The loop the owner's first message hopes for needs a cell to build that way at least once.

[F] **8. Three of the nine predictions failed.** Stack did not end clearly ahead of free. Builders made an edit in 55 of 90 turns, under the 75 percent expected. Of the 28 turns without an edit that were read, 15 ran out of calls before anything was written and 11 stopped with the target already at or near a full score. And no candidate failed to boot in the block, though one did in the excluded warm run. The gate discarded 7 of the 58 candidates that reached it.

**What the pilot does not show.** [I] It has a ceiling. Once every arm sits near the top after one or two builds, the arms have little room to differ, so "the controls matched" is weak evidence that they would match where improvement is hard. Cutting the calls a task gives does not buy room either: given one call in place of three, 13 of the 28 final harnesses measured still score 0.77 to 0.97. So the next block needs harder tasks, not fewer calls.

## Published work

[K] A search helper looked for the nearest published work on 2026-11-17 and opened the sources it lists. The lead did not open them again, so each line is the helper's reading. "Not found" means not found in that search. The queries covered self-editing agents, agents that build other agents' tools, co-evolving pairs, and blue-green updates between agents.

- **No source was found that has both parts of the proposal:** a cell that may edit only its peer, and two cells that take turns doing so. None compares cross, rival and shared scoring.
- **Nearest.** Escher-Loop (Liu et al., 2026, arXiv 2604.23472, opened in full): a population of optimizers that edit task agents, each other and themselves, scored by Elo. It allows self-editing and has no twins.
- **One-way builders.** ADAS (Hu, Lu and Clune, 2024, arXiv 2408.08435, abstract), Meta-Harness (Lee et al., 2026, arXiv 2603.28052, full) and LATM (Cai et al., 2023, arXiv 2305.17126, abstract): a fixed agent writes another agent's harness or tools, and nothing comes back.
- **Self-editors.** Darwin Gödel Machine (Zhang et al., 2025, arXiv 2505.22954, full), SICA (Robeyns et al., 2025, arXiv 2504.15228, full), Gödel Agent (Yin et al., 2024, arXiv 2410.04444, abstract): one agent edits its own code, with an archive of variants. These are the single-cell case.
- **On the pilot's two main readings.** Jha, Kleiman-Weiner and Jaques (2026, arXiv 2609.38516, full) found that populations of agents sharing skill files did not beat solo learners at matched cost. The Darwin Gödel Machine's ablation with a fixed meta-agent gained early and tapered off, while the full system kept improving over 80 iterations. So fast saturation and "solo matches social" both have published company, and both have counter-examples.
- **On gaming.** The Darwin Gödel Machine's authors report an agent that removed the markers its hallucination check relied on. RewardHackingAgents (Atinafu and Cohen, 2026, arXiv 2603.11337, full) reports evaluator tampering attempted in about half of episodes, and none once the evaluator was locked by hash. These bear on the referee's two open weaknesses listed in the record.

## Transposition

The pull request asks for the concepts to be crossed with ideas from the other repositories. Siliquant pull request 5 (`notes/cross-org-grafts.md` there) already made that pass for siliquant, over about 230 repositories in five organisations, and lists the mechanisms it found. This note takes its list as the columns and does not repeat the triage. A mechanism marked **checked** was re-read in source for this note. One marked **reported** is taken from the siliquant note as it stands.

The method is the same: each concept of the proposal is crossed with each mechanism, and a crossing is kept only if it changes the design or gives a first test.

**Concepts of the proposal (rows)**

- T1. The relay: one cell edits, the other runs the result.
- T2. The referee outside both cells: benchmark, limits, sandbox.
- T3. The gate on a change.
- T4. The score and what it rewards.
- T5. Free or stacked changes.
- T6. The cap on harness size.
- T7. What the benchmark draws.
- T8. The proposal's own claims.

**Mechanisms (columns)**

- W1. Bounded change measured from a saved baseline, not from the last step. (weft, `plasm.py`) **Checked:** the baseline is saved once at `plasm.py:350` and passed to the gate at `:423`.
- W2. A budget checked before the commit, and a rejected update changes nothing. (weft, `invariants.py`) **Checked** in `verify_weight_update_safety_ex`: the budget tests come first, and a reject for distance leaves the budget as it was. The C header debits the budget on two reject paths (`weft_invariants.h:135`, `:140`), which the recheck record discusses.
- W3. Two candidates scored, and the winner must still pass the gate. (weft, `plasm.py:412-436`) **Checked.**
- W4. One file of test vectors read by independent implementations. (weft, `invariants/vectors.json`) **Checked:** 27 cases, read by Python, C and JavaScript.
- C1. Probes drawn only after the candidate is committed. (weft-loom, `committed-behaviour-change-2026-11-15/cbc.py`, `probe_seed`) **Checked.**
- C2. A path is closed only on a certificate. (weft-loom, `notes/closure-by-certificate.md`) **Checked.**
- R1. An arm with the same information and none of the mechanism. (weft-loom, `weft-threads-recheck-2026-11-15`) **Checked.**
- R2. Report how often each mechanism changed an outcome. (same record) **Checked.**
- L1. Shown prices move a cell's first act. Heirs that inherit a body stop searching. (weft-loom, `razi-cells-laws-2026-11`) **Checked** in the record's README.
- O6. Density-survival ratio: realised saving over nominal saving. (tokenpage) **Reported.**
- O8. Approval bound to a hash of the reviewed text, plus rerun-and-diff. (mission) **Reported.**
- O11. Generate the table from the data, then assert equality. (protean-drafts) **Reported.**
- O12. Certificate or nothing: a claim counts only if its witness verifies. (tar, cedar) **Reported.**
- X2s. A preregistration gate: the plan's commit must come before the first output. (siliquant note, graft X2) **Reported.**

Added 2026-11-24, from work merged or opened in weft-loom since the first version of this note:

- K1. LoRA training on Tinker from a list of examples, with the adapter sampled from right after. (weft-loom pull request 46, open, which ran it once for 0.09 dollars) **Checked** in that pull request's description.
- K2. Mutation testing of a record's guards: remove each guard and show a test fails. (pull requests 38 and 46, open) **Checked** in their descriptions.
- K3. Exact feedback did not speed repair: telling a model the signed amount by which each constraint failed did not let it repair in fewer rounds than naming the constraint and place. (pull request 38, open, both registered runs "not decided" or against) **Checked** in that pull request's description.

**Crossings**

| # | Crossing | What it gives | State |
|---|---|---|---|
| G1 | T3 × W1 | Gate against the old harness measured again, not against its last recorded score. A margin applied step by step lets a run walk downhill one margin at a time. The siliquant note found the same defect in weft-eido's radius gate. The reply's safeguard 3 has it as written | **Built.** Each gate runs the old and the new harness on the same fresh tasks |
| G2 | T7 × C1 | Benchmark tasks drawn after the candidate is fixed, from a seed that mixes a per-run secret with the candidate's hash. The secret is logged when the run ends | **Built** (`relay.instances`) |
| G3 | T1 × R1 | The arm that decides whether the twin does anything: each cell edits its own harness and the same referee restarts and gates it | **Built** (arm `solo-pair`) |
| G4 | T1 × R1 | The arm that decides whether a better harness makes a better builder: every build turn runs in the unchanged seed | **Built** (arm `twin-fixed-builder`) |
| G5 | T3 × W2, O12 | A discarded candidate changes nothing. Calls are counted before the model is asked, so no turn can overdraw (lesson K13 of the laws record) | **Built** (`brain.BrainServer`) |
| G6 | T2 × O8 | Every harness is stored under the hash of its tree. A log row names the builder's harness, the base, the candidate and the result by hash, so a kept change is bound to the tree that was benchmarked | **Built** (`bench.Store`) |
| G7 | T8 × C2 | The reply's incentive claims read as closures. A scoring rule is closed for "building the twin's builder" if a proof shows that it never pays to | **Built** as the prototype. It closes cross and rival scoring under stated assumptions |
| G8 | T3, T5 × R2 | Count how often each part acted: candidates kept, discarded at boot, discarded for a lower score, turns with no edit, pairs whose two harnesses differ at the end | **Built** (`analyze.py`) |
| G9 | T6 × O6 | The size of a harness beside what it gained | **Built** as two columns. The pilot's final harnesses were 5.1 to 6.8 kilobytes on average by arm, against the seed's 4.1, for a gain of about 0.45 |
| G10 | T8 × O11, X2s | The record's plan is committed before its first run, and its tables are written from the logs by a program | **Built** |
| G11 | T2 × W4 | Each task family has a second solver that reads only the instance files and must reproduce the hidden truth exactly on every seed tested | **Built** (`referee/tasks/selftest.py`) |
| G12 | T3 × W3 | Two candidates per turn, from two builders or two tries, with the better one sent to the gate | Not built. First test: one arm at twice the build cost |
| G13 | T4 × L1 | A builder shown the price of its own build calls. Shown prices moved 26 of 32 cells at their first act | Not built. First test: the brief with and without one price line |
| G14 | T5 × L1 | Stack is inheritance of the whole line. In L1 inheritance anchored: on one task blank cells reached the ceiling 2 of 3 times and heirs 0 of 3. So stack may stop exploring sooner than free | Seen once, as a description: with the scoreboard high, stack builders made an edit in 1 of 11 turns and free builders in 5 of 9. First test: the same count on a benchmark with room |
| G15 | T1 × K1 | A cell's harness includes a small adapter, and the builder writes training examples for its twin's adapter as well as text. That carries the proposal from prompts to weights, where Tinker makes a turn cheap | Not built. First test: one turn, the builder's examples against random examples from the same tasks, on one adapter each |
| G16 | T2 × K2 | Every guard of the referee is removed in turn and a test must fail | **Built** (the record's `block2/mutate.py`: 30 of 30 caught, after its first run found one gap and a test closed it) |
| G17 | T2 × O8 | A paid run starts only with an approval bound to the hash of the plan text and the run's tag | **Built** (the record's `run.py`, `check_approval`) |
| G18 | T4 × K3 | The builder's report: K3 suggests that a more detailed failure signal does not by itself make repair faster. The pilot's builders got scores and traces | Not built. First test: the block 2 assay with and without the traces in the report |

The mathematical mechanisms in the siliquant list gave no crossing with a first test: lattice decoders, permanents, Delsarte ceilings, the zero-vector recurrence, Krawczyk enclosures, interval subdivision and Schur-complement relaxation. They are about weights and counts, and the proposal is about agent harnesses.

## What would decide it

In order of information for the effort. Updated 2026-11-24: item 3 is done, and a new first item comes before the others because it is the cheapest.

1. **Measure the building gap again.** Fact 5 is the pilot's sharpest result and was found after the runs. Each harness was assayed once, slot A only. Part A of the block 2 plan assays the 19 fault-free final harnesses again, both slots, three fresh assays each, with the predictions, analysis and power fixed beforehand, for about 10 dollars at list. The assay starts every harness from the seed at about 0.5, so it has the room the exam lacks. If free lineages still build worse than both controls, the reciprocal loop is not just absent but reversed under the arrangement the owner's first iteration chose, and item 3 below is the place to look for why.
2. **A benchmark with room.** Harder task families, built so that a harness which already shows the notes and uses its calls well sits near 0.5, and a block that starts from a harness the pilot's cells built. Until then no arm can be told from another. The power figures of the recheck apply: a difference of 0.10 between arms needs tens of runs, not three.
3. **Put building in the gate.** The pilot's gate measures only task scores, so a change that halves a cell's building is kept if the tasks still pass. A standing builder assay, even a small one every second turn, would have caught the step limit of 12. Without it the proposal's central quantity is not measured where decisions are made.
4. **Close the two holes the second reader found before any run where a cell could gain from them.** Done 2026-11-24, offline. The pilot's checker did accept forgeries: given generated instances, it scores code that calls the hidden script's reporting function 1.000 in both code families. The new checker gives the cell's code only the inputs and compares results in the referee, and on 2,520 honest instances it agrees with the old one on every score. An episode is now charged only for the cell's own time, not for waiting on the model. A mutation check removes 30 of the referee's guards one at a time and a test catches each. The record's block 2 section has the files.
5. **Follow the one contrast with a direction.** Live builder against seed builder, on the harder benchmark, with the assay beside it. If the exam says a live builder ends ahead and the assay says its harness builds worse, one of the two measures is not measuring what it is named for.
6. **Test fact 5 of the model directly.** Run rival scoring twice: once with the gate drawing the families the builder has seen, once with families it has not. The model says the family-specific advice should go away in the second.
7. **A tighter gate.** With nothing changed, the gate's score difference has a standard deviation of 0.072, and it kept 2 of 6 identical candidates. More tasks per gate, or a second look before a discard.
8. **Then the variations not run:** selection among pairs, the two-phase schedule, two candidates per turn, a price line in the brief, a second model family, and G15 below.

## Open questions

1. Does a language model in a harness answer to a stated scoring rule at all, beyond its wording? The pilot's rival arm suggests the wording moves what is written. It cannot say whether a payoff would.
2. Is there any benchmark on which a narrow tool beats a general one for a cell that reads the task notes anyway? If not, `G` is above 2 in practice, the dilemma of the model never arises, and scoring schemes are beside the point.
3. Why did builders stop at a full score on 9 tasks? A cell shown a perfect scoreboard has no reason to look further, which is lesson K20 of the laws record in another form. Would a scoreboard that reports the exam's spread keep them working?
4. What is the unit that compounds, if anything does: tools, prompt advice, or notes passed between cells? No cell left a note and none added a tool file. A harness with a shelf for either might be needed before the question can be asked.
5. Is the stack rule's one line a strength or a risk once the gate is noisy? One bad kept change reaches both cells within two turns.

## Limits

- The model is a model. Its cells maximise a payoff, know the horizon and never err. Nothing in it is a statement about a language model.
- The pilot is one model, one machine, one day, 4 runs per arm and 6 turns. It reads direction and size. It cannot show that two arms are equal.
- The benchmark is five families of generated tasks with 3 model calls each. A good harness there is mostly one that reads the instance notes whole and does more per call. Other benchmarks would reward other things.
- The model is reached through a command line tool that adds its own notes to every call. The referee counters that with one fixed line. The record says what was seen and done.
- The mechanisms marked reported in the transposition were not re-read here.
- Decimal figures in the sections drawn from the record are checked by a program to equal some number in an output file. Tested by planting errors, that check caught 17 of 60 small ones in this note (the record's README, limits). It guards against invented figures more than mistyped ones.

## Disclosure

Written by an AI agent session after the owner handed the programme over on 2026-11-17. The same session added the 2026-11-24 changes after the owner asked it to pick the work up again. The prototype game and the task families were written by two further agent sessions from written briefs. Three more recounted the logs, coded what builders changed, and searched for published work. The lead re-solved every case of the game with a second program, and ran the calibration, the pilot and the analysis. No person has reviewed this note or its record.
