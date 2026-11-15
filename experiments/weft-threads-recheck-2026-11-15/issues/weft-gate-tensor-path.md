## Finding

`verify_weight_update_safety_ex` has a fast path for torch tensors. It subtracts the two tensors and takes `torch.linalg.norm` in their own type, which is float32 in Plasm. The list path sums squares in float64.

Near the radius the two paths disagree. The tensor path accepts moves whose exact distance is above the radius.

## Evidence

Checked on main at `aada4c6`, 2026-11-15.

- Exact check: 199 float32 weight pairs with the radius set between the float32 norm and the exact distance, computed with rational arithmetic. The tensor path accepted all 199. The list path rejected all 199. The largest excess over the radius was 1.0e-7 relative.
- A differential test of the Python, C and JavaScript gates on 20,992 inputs found 255 such accepts by the tensor path, and 13 cases the other way. The Python list path and the JavaScript gate agreed on every accept decision.
- The same path overflows float32 on the shared vector `accept_huge_scale_weight_move` and reports `non_finite_weights`. `test_invariants.py` skips that vector and `reject_pre_cast_radius_boundary` when it tests tensors.
- `plasm.py` calls the gate with tensors, so this is the path the Plasm cycle uses.
- `weft.runtime.plasm.test_mps_baseline.test_live_check_mps` fails on an Apple Silicon Mac with `DIFF /e4_conformance/python_agrees: 14 != 15`. CI skips that test on Linux, so the one platform that runs it is red on main.

## Size

Small: about one part in ten million, at the boundary only. It matters because the gate is presented as one predicate in three languages, tested on shared vectors, and this path is outside that test.

## Reproduction

`runtime/tensor_path_repro.py` in the weft-loom record `experiments/weft-threads-recheck-2026-11-15`. It needs NumPy and PyTorch.

```
python3 tensor_path_repro.py --weft /path/to/weft
```

It prints the count of accepts and exits with status 1 while the defect is present.

## Proposed fix

Cast both tensors to float64 before the subtraction, or send tensors through the list path. Then run all 15 weight vectors through the tensor path in `test_invariants.py` with no skips.

The docs could also state what an accept guarantees. With float64 accumulation over `n` weights, an accepted move has an exact distance of at most `R (1 + e)`, with `e` about `(n / 2 + 2) * 1.1e-16`.

## Acceptance

- The reproduction prints 0 accepts by the tensor path.
- No weight vector is skipped for tensors.
- `test_live_check_mps` passes on a Mac with MPS.

> Automated posting by agentic team with human oversight.
