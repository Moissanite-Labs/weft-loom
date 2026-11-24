# Preregistration: gemini-cells relay pilot

Written 2026-11-17, after the instrument calibration in `results/calibration.jsonl` and before any relay run. This file, the harness and the analysis script are committed and pushed before the first run. The frozen file hashes are at the end.

The proposal under test is in weft-loom pull request 27 and in [`notes/gemini-cells.md`](../../notes/gemini-cells.md).

## Question

Two twin cells take turns. On its turn a cell cannot change its own harness. It edits its twin's, the referee restarts the twin on the result, and both are benchmarked.

1. Does this end with better harnesses than two cells that each edit their own harness under the same referee?
2. Does a cell that has been given a better harness build better than a cell left in the seed?
3. Among the three arrangements the owner proposed, does any end ahead?

## Instrument

A **cell** is `claude-haiku-5-5` inside a harness: a folder with `agent.py`, a prompt and tool files. The seed harness in `seed/` has three actions (run a shell command, write a file, finish), one action per model call, and 1,200 characters of tool output shown back. A task gives the harness 3 model calls and 16,000 characters per prompt, enforced by the referee.

A **task** is a folder holding one generated instance. The cell must leave an answer there, and a checker it never sees scores it from 0 to 1. Three families are used for the gate (`ledger`, `logwin`, `bugfix`) and two more only in the final exam (`stock`, `spec`). Rules inside a task change from instance to instance. Every task here is generated at level 3, the hardest. `referee/tasks/selftest.py` checks every family on 60 seeds at three levels.

The **referee** sits outside the sandbox. It holds the task generators and checkers, counts model calls, caps prompt length, and decides what is kept. A cell runs with no network, no credentials and one writable folder (`results/sandbox_selftest.out`, 26 of 26 checks).

A **build turn** gives the builder cell 16 model calls, 30,000 characters per prompt, a copy of a target harness, the target's last benchmark report with traces, one example task per gate family, and a brief. Whatever is in `target/` when the turn ends is the candidate.

The **gate**, for a candidate that differs from the target's harness:

1. Surface rules: `agent.py` present, at most 60,000 bytes and 24 files, symlinks removed.
2. Boot: one live episode of a trivial task with 3 model calls.
3. Paired benchmark: the old and the new harness each run the same 9 fresh tasks, 3 per gate family. The task seeds come from a hash of a per-run secret and the candidate's tree hash, so they are fixed only after the candidate is.
4. Keep the candidate if its mean is at least the old mean minus 0.02. Otherwise the old harness stays.

## Arms

| Arm | Who edits what | Candidate starts from | Builder runs in | Scoring paragraph of the brief |
|---|---|---|---|---|
| `twin-free-rival` | the twin's harness | the twin's harness | its own harness | scored on the twin's benchmark, higher score wins |
| `twin-free-collective` | the twin's harness | the twin's harness | its own harness | one score for the pair |
| `twin-stack-collective` | the twin's harness | the builder's own harness | its own harness | one score for the pair |
| `solo-pair` | its own harness | its own harness | its own harness | scored on its own benchmark |
| `twin-fixed-builder` | the twin's harness | the twin's harness | the seed, every turn | one score for the pair |

The first three are the owner's first proposal and the two iterations of the second message. The last two are controls. `solo-pair` has the same referee, gate, report and number of edits, and no twin. `twin-fixed-builder` gets the same brief, word for word, as `twin-free-collective`. Its sentence saying that the twin will build in the harness it is given is not true in that arm, and that is the manipulation: no builder there ever leaves the seed.

Every run has 6 turns, 3 builds per cell slot, cell A first. Each run starts with one benchmark of the seed per slot on its own fresh tasks.

4 runs per arm, 20 runs in all. They are launched replicate by replicate: the five arms of replicate 0 side by side, then replicate 1 once those have finished, and so on. A replicate starts only if at least 5 dollars are left under the spend cap. If that stops the block early, or the cap stops a replicate part way, only replicates that finished in all five arms are analysed. The builder assays run last, replicate by replicate, on what is left under the cap. If they cannot cover every run, P9 is judged on the runs they cover.

One warm run was made before this file was written, to shake the relay down (`twin-free-collective`, 2 turns, a 10-task exam). It ran on task modules that changed afterwards and is excluded from every count. Its log is kept in `results/warm/`.

## Calibration

Run before this file was written, on the frozen task modules. `results/` holds the outputs.

- **The seed on the exam, 12 sittings.** Visible mean 0.501, with a standard deviation of 0.045 between sittings (lowest 0.427, highest 0.584). Held-out mean 0.524, standard deviation 0.132 (lowest 0.373, highest 0.849). The held-out measure is the noisier one: it has 12 tasks against 24, and the `spec` family is close to all or nothing. `results/seed_exam.json`.
- **A harness written by the lead, on the same exam, 2 sittings.** `calibration/ref-harness/` runs every action in a reply and shows the folder listing and the instance notes in the first prompt. Visible 0.917, 0.807, held-out 0.833, 0.750, with 1.28 model calls per task. So the benchmark tells a bare harness from a better one by about 0.36 on the visible families, and a level near 0.86 is known to be reachable. `results/ref_exam.json`.
- **The gate with nothing changed, 6 trials.** The seed against itself on the same 9 fresh tasks: the second score minus the first had mean -0.040 and standard deviation 0.072, and the gate would have kept 2 of 6. So a candidate that changes nothing is discarded about as often as it is kept, and the gate is a coarse filter. `results/gate_noise.json`.
- **Why 3 calls and level 3.** The seed on 4 tasks of each of the five families (`results/calibration.jsonl`):

| Calls per task | Level | Seed mean, 20 tasks |
|---|---|---|
| 5 | 3 | 0.726 |
| 2 | 3 | 0.406 |
| 3 | 2 | 0.670 |

  The exam above is the point with 3 calls at level 3, where the seed sits near the middle of the scale. With 5 calls the seed already reaches 0.73, which leaves a builder less to find.

## Measures

For each run, after turn 6, the final harness of each slot sits the **exam**: 8 fixed instances of each gate family and 6 of each held-out family, the same 36 instances for every run and arm, never used in a turn. If the two slots end on the same harness, it sits the exam once and the score counts for both.

- **M1, visible.** The mean exam score on the gate families, averaged over the two slots.
- **M2, held-out.** The same on the two held-out families.
- **M3, what acted.** Per arm: candidates kept, discarded at boot, discarded for a lower score, discarded by the surface rules, turns with no change, turns where the builder made an edit, and pairs whose two final harnesses differ.
- **M4, builder assay.** The final harness of slot A of every run takes one build turn on a fresh seed harness under the collective brief. The measure is the candidate's mean minus the seed's mean on the same 9 fresh tasks, counted as 0 when the candidate is discarded before the benchmark.
- **M5, cost.** Model calls and dollars per run, from the ledger. Also the model calls used per exam task and the size of the final harnesses, as descriptions with no pass mark.

The seed's level on the exam is the mean of its 12 sittings in the calibration.

## Predictions

Written before any relay run. Each has a pass mark. "Ahead by 0.10" means a difference of arm means of M1 of at least 0.10.

- **P1, the instrument works.** In every arm the mean of M1 is at least 0.10 above the seed's exam mean. If this fails in every arm the relay did not improve harnesses and the contrasts below say nothing.
- **P2, the twin adds nothing over a referee.** `twin-free-collective` and `solo-pair` end within 0.10 of each other on M1. The reply in pull request 27 says the opposite: that the twin "directly solves" the restart problem. Its own third safeguard, a referee that checkpoints and reverts, gives a single cell the same protection.
- **P3, no compounding in 6 turns.** `twin-free-collective` and `twin-fixed-builder` end within 0.10 of each other on M1. The owner's first message expects the opposite in the long run: better tooling makes a better builder.
- **P4, stack ends ahead of free.** `twin-stack-collective` minus `twin-free-collective` is above 0.03 on M1. Under stack every kept change reaches both cells. The reply predicts the same direction.
- **P5, the scoring paragraph does not matter.** `twin-free-rival` and `twin-free-collective` end within 0.10 of each other on M1 and on M2.
- **P6, builders act.** Across all arms, the builder makes an edit in at least 75 percent of build turns. In the heredity runs of the laws record, 65 of 70 heirs changed nothing.
- **P7, the gate acts.** Across all arms, at least 10 percent of candidates that reach the gate are discarded, and at least one is discarded at boot.
- **P8, gains carry to unseen families.** Pooled over all runs, the mean gain of M2 over the seed is at least half the mean gain of M1 over the seed. A cage of narrow solvers for the three gate families would show as a visible gain with no held-out gain.
- **P9, a built harness is not a better builder.** The mean of M4 over the four arms other than `twin-fixed-builder` is within 0.10 of the mean first-turn gain of seed builders in this block. That is turn 1 of every run, where a seed cell edits a seed harness, with the gain counted the same way as M4.

## Analysis

`analyze.py`, frozen below, reads the run logs and writes `results/tables.md`. The unit is the run. Each contrast is reported as a difference of arm means with an exact two-sided permutation p over the run labels.

With 4 runs per arm the smallest two-sided exact p is 2 in 70, or 0.029, reached only when every run of one arm is above every run of the other. Anything short of that is direction and size, not a test passed.

A prediction that says "within 0.10" passes on the difference of means alone. It is a statement about size, not a test, and with this many runs it cannot show that two arms are equal.

## Exclusions and stops

- A run is excluded only for a referee fault: the model backend failing, or the sandbox failing to start. The reason is recorded and the log kept.
- A run that ends early because the spend cap was reached is reported as incomplete and not replaced.
- No run is repeated because of its result.

## Spend

One model, `claude-haiku-5-5`, called through the `claude` command line tool with tools off and thinking off. The cap is 25 dollars for the whole record, calibration included, enforced by the ledger in `referee/brain.py`. Spent before this file was committed, on smoke tests, the warm run and the calibration: 2.72 dollars over 2464 model calls. The block of 20 runs with its builder assays is estimated at 19 dollars from the cost of the warm run.

Ownership of the programme was handed to the agent session that wrote this file on 2026-11-17. The session set the cap itself and told the owner before the first relay run. The earlier colony pilot ran under the same cap with the owner's approval.

## Frozen files

SHA-256 of each file as it stood when this plan was committed. `sha256sum -c` style, paths from this folder.

```
4f8197924f436835d1b2da8069efe297146d7e61b1f4ac139f6d8d51c7d77a32  analyze.py
084e104321f900b4e3ef5d2c663e834bc99c60fbca8f2586f3d054f970401939  calibration/ref-harness/agent.py
2c6f3ecd9c8084783177b6cb22695a83905c8af6e54ee5d2b440c0a093ed1136  calibration/ref-harness/prompt.md
dda30265847d69923febab964fc71fd65783045fd0069c98d237abcd64bb54aa  calibration/ref-harness/tools/sh.py
733ec3b15b28f9b41e6ef4e7754bf5c6cd2861fd02fdaf3ec245b9315c2baf2d  calibration/ref-harness/tools/write.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  referee/__init__.py
e57011dd3853a9540dc2900bfca38a2c63edf78265f627de4f2d6eb10308d262  referee/bench.py
3720a7aa8c19c8d4a2f8914bbff07876599461ef9f16710af16283d7d604de7b  referee/brain.py
435508c50868135850ae5b381a3f56b6e2d10fa6c1ade56811d9c6b07049ce57  referee/cellapi.py
0d9da6881a5b66cda61818e4ada46a6f80d412fea854d90abbaeae241e67164d  referee/relay.py
cfa147ca65ef7b4fc7dd3856c56ae0316cb62aa36d94335d69055d405ca7d0f9  referee/sandbox.py
4dba49eba87f053187017696c996ecca887ad2eb64c406a3eefab66348507372  referee/tasks/__init__.py
7e5ab0dd1a23167922e9f9fe0c7b28ef7f50f6cf697219ea0528f17349af088a  referee/tasks/_bugpool_a.py
b299eb899d4ee19eab4a5aadde7cddbf2c403779d332a6dce4642225029f995d  referee/tasks/_bugpool_b.py
21e2e17f900296a3a904c8880f6d383dcf7d67a14f7453d584bfa6827ad79a12  referee/tasks/_specpool_a.py
659bf881ecb0da7cd1dc3ddcdc2081c99517b8dca1bd63d384d81d813732bf1c  referee/tasks/_specpool_b.py
80afcfd2e604240d179b66d941c4a32779119a6d16489fe4be7641d6ec61caf0  referee/tasks/_util.py
ef8dcbccdf569118f53c825870c6a208b7e734fcda084edaa5eb3523e438199d  referee/tasks/bugfix.py
9b1a1132c7a9f95a4e2553f5bd449f1b711cc9fc3acf8d1c2cc1af7d41ad66e8  referee/tasks/ledger.py
c27ed2f3844d5987bf3dfeb91b237fae9139c6046adbab5e48e38f6befcb5041  referee/tasks/logwin.py
9655ab900b95adfd1b9f72b0acb2dee1d8737e3804312c1ec75af4e8a7fbe50a  referee/tasks/selftest.py
56084dcd26567630428e3493ed50258e8e84b48031bb9678715b28eacb579c2c  referee/tasks/spec.py
be1015fd12f7d5b298a407c7bc301deb587b0c55f81bac3001709a2e932316b5  referee/tasks/stock.py
9d6fc2e43d8e6ff7911979ddcc9c726e9feadad36466d0e5906321a775adec49  run.py
ba894b5afd76df787bec3bfbdfa42c7a76fb1bc77ed931b10dfd9397affe3f93  seed/agent.py
9f85ed0362874950eea83c76d53d38867db2b9b61725281d5ebf561f49fadb7d  seed/prompt.md
dda30265847d69923febab964fc71fd65783045fd0069c98d237abcd64bb54aa  seed/tools/sh.py
733ec3b15b28f9b41e6ef4e7754bf5c6cd2861fd02fdaf3ec245b9315c2baf2d  seed/tools/write.py
```
