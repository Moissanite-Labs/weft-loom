Capability: WEFT-T1 gate metric. This record feeds radius work in the weft repo.

## Question

The gate bounds weight distance from a baseline. Does that distance track behavior change at all?

Weight space has exact symmetries. Permuting hidden units changes every weight and no output.

## Probe result, 2026-11-15

One trained E13 host. Fresh shifted batch. Host weight norm 20.811. Native shifted R2 0.8981.

Permutation: distance 28.861. Output change 0.000000. Native R2 stays 0.8981.

Random move at the same distance 28.86: output RMS change 7.46 on average. The model is destroyed.

Random moves scale smoothly. Distance 0.1 gives 0.014. Distance 1.0 gives 0.145. Distance 5.0 gives 0.749.

Readout sign flip: distance 6.640. Output RMS change 4.97. Native R2 falls to minus 2.94.

The flip sits inside a radius 10 ball. Both shipped defaults accept it. The permutation is rejected at radius 10 and accepted at 120.

Raw distance is neither needed nor enough for behavior safety in this harness.

## Proposed work

Preregister a calibration study before running it.

Sweep update directions: random, gradient, adversarial, permutation and scaling gauges.

Plot behavior change against four distances. Use Frobenius, Fisher-weighted, output RMS on probes, and output divergence.

Repeat on a second architecture. A tiny transformer is enough.

Pass mark: one distance predicts behavior change within a stated factor across directions.

Fail mark: no distance beats Frobenius by that factor. Then the gate needs a behavior check, not a better norm.

The result decides how radius work in weft should set its bound. It also gates any hardware comparator design.

> Automated posting by agentic team with human oversight.

