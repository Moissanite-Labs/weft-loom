# Weft threads coordination workspace

Outcome: find where Weft treads new ground, what outsiders would value, and which threads repay pulling. Success means each surviving thread has one decisive test on record in its own repo.

Scope: `Moissanite-Labs/weft`, `weft-loom`, `weft-eido`, `weft-corpus`, `abios`, plus consumers in `exo`. Local snapshots: weft `1f8b611` (2026-11-08), loom (2026-11-13). GitHub main was checked for issue state, not re-read line by line.

## Repository map

- `weft`: software. Runtime C1 to C7, site, papers, claims register. Home for gate, Plasm, IC, ledger fixes.
- `weft-loom`: science record. Experiments, audits, preregistrations. Home for E13, colony laws, method studies.
- `weft-eido`: design language modules. Telemetry and packet fixes stay in `weft`.
- `abios`: SYM-2P packet spec and validators. Three forms share one name today.
- `exo`: agent harness. Consumer for colony price laws after replication passes.
- `siliconcordat`: org record. Synthesis and decisions for A live here.

## Thread status (2026-11-15 evaluation)

- WEFT-T1 safety gate: known-art. Sound predicate, broken parity. Existing: weft #74, #42. New: weft #210 (C reject debit). Status: ready.
- WEFT-T2 Plasm cells: known-art. Masked fine-tuning plus watermark. Existing: weft #75, #51. Status: proposed.
- WEFT-T3 plasmid splicing: thread-to-pull. Wire-only passed 12 of 12 on 2026-11-15. New: loom #6. Scale home: weft #142. Status: ready.
- WEFT-T4 colony laws: thread-to-pull. Price law real, sense law unproven. New: loom #8. Status: ready.
- WEFT-T5 interaction combinators: thread-to-pull. Reducer sound, verifier missing. Existing: weft #77, #43. Status: ready.
- WEFT-T6 abios packets: thread-to-pull. Encoding known-art, net saving unmeasured. New: abios #52. Adjacent: abios #50. Status: ready.
- WEFT-T7 Eido and telemetry: known-art. Existing: weft #45, #67. Status: proposed.
- WEFT-T8 evidence method: thread-to-pull. Works in tranche, decays after. New: loom #9. Status: ready.
- WEFT-T9 ledger, OS, silicon: thread-to-pull for one kernel only. Existing: weft #44. OS and silicon stay design branches. Status: blocked on radius pin for comparator work.

## Convergences, ranked by information per week

- R1 gate as splice admission (T1 x T3). Needs radius pin first. Use behavior distance if calibration supports it.
- R2 fail-closed packets for telemetry display (T6 x T7). One day once packet form is picked.
- R3 price packets in compact form (T4 x T6). Half a day plus API spend. Needs loom #8 design.
- R4 replay verifier as evidence receipt (T5 x T8). Two to three days. Needs weft #77 verifier.
- R5 watermark-bound lineage payouts (T2 x T9). Needs secret seed redesign and weft #44.
- R6 learned router for the shunt (T3 x T4). Most likely to fail. Run only after loom #6 controls.

## Calibration gap (cross-cutting)

Probe 2026-11-15: permutation distance 28.861, behavior change 0. Readout flip distance 6.640, R2 0.8981 to minus 2.94. Record: loom #7. This finding sits under T1, T2, T3 and T9.

## Checkpoint (updated 2026-11-15, thread-pulling round)

Pulled this round: hardening (loom #10), behavior admission (loom #11), colony readiness (loom #12).

Splice status now: distinct worlds 11/12, width 160k MLP 6/6, transformer 272k position-wise skill 1.0 all skills (2/2 seeds), routing skill blocked pending attention graft. Router-from-content impossible in E13 world by construction.

Admission design: donor agreement plus held-out native drift. Shipped radii accept 47/48 and 0/48 on the graft set. Behavior checks cover all harm classes tested, benign 12/12.

Next ready action: attention-head graft design for routing skills, then a small pretrained model. Colony scrambled control waits on a small live-spend approval.

Bottleneck: radius and metric decision for A still open in siliconcordat #16. Behavior admission evidence now informs that call.

Probes kept here: `probes/e13_wireonly.py`, `probes/calibration_probe.py`, `probes/hardening.py`, `probes/intersections.py`, `probes/donor_agreement.py`, `probes/scale_probe.py`, `probes/tf_splice.py` to `tf_splice3.py`. Issue drafts kept in `issues/`.

Team route: Divan group message seq 1676 opened the round. No seat replies had arrived at the last inbox check.
