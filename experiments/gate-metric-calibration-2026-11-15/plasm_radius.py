#!/usr/bin/env python3
"""What the gate radius means for the linear Plasm cell of the weft runtime.

The Plasm cell computes out = x W for a square matrix W. For a linear map the
gate's Frobenius bound is an exact behaviour bound (README, "The linear cell"):

    for every input x:      ||x dW||_2 <= ||x||_2 ||dW||_F      and equality is reached
    on a stimulus set X:    RMS change <= R smax(X) / sqrt(n d)  and equality is reached

This program evaluates both for the stimulus and weights that
run_weft_plasm_cycle builds, checks the equality by constructing the worst
move, and prints the radius that keeps the change under a stated share of the
cell's own output.

Usage: python3 plasm_radius.py --weft /path/to/weft/checkout
Exploratory: not part of the preregistration.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weft", default=os.environ.get("WEFT_CHECKOUT"))
    ap.add_argument("--out", default="plasm_radius.json")
    a = ap.parse_args()
    if not a.weft or not (Path(a.weft) / "weft" / "runtime" / "plasm" / "plasm.py").exists():
        raise SystemExit("give the weft checkout with --weft or WEFT_CHECKOUT")
    sys.path.insert(0, str(Path(a.weft).resolve()))
    sys.dont_write_bytecode = True
    import torch
    import weft.runtime.plasm.plasm as plasm
    from weft.runtime.invariants import R_INVARIANT

    torch.set_default_dtype(torch.float32)
    dev = torch.device("cpu")
    arena = plasm.StratifiedAppleSiliconPlasm(name=f"weft_rad_{os.getpid()}", create=True)
    try:
        arena.seed_arena()
        w_core, _, _ = arena.read_tensors_to_device(dev)
        dim = w_core.shape[0]
        core_rows = dim // 4
        w_core, _, _, _ = plasm.embed_weight_watermark(w_core, seed_phrase=None, core_rows=core_rows)
        w0 = w_core.detach().clone().double()
        gen = torch.Generator(device="cpu")
        gen.manual_seed(20261107)                      # the seed the cycle uses
        x = (torch.randn(16, dim, generator=gen, dtype=torch.float32) * 0.25).double()
    finally:
        arena.release_views()
        arena.close(unlink=True)

    n, d = x.shape
    out0 = x @ w0
    out_rms = float(out0.pow(2).mean().sqrt())
    smax = float(torch.linalg.svdvals(x)[0])
    per_unit = smax / math.sqrt(n * d)                  # worst RMS change per unit of distance
    xnorm = float(x.norm(dim=1).max())

    # The worst move of length 1: u v' with u the top right-singular vector of X.
    _, _, vh = torch.linalg.svd(x, full_matrices=False)
    u = vh[0]
    dW = torch.outer(u, torch.ones(d, dtype=torch.float64) / math.sqrt(d))
    if abs(float(dW.norm()) - 1.0) > 1e-12:
        raise SystemExit("FAIL: worst move does not have length 1")
    reached = float((x @ dW).pow(2).mean().sqrt())
    if abs(reached - per_unit) > 1e-12 * per_unit:
        raise SystemExit(f"FAIL: bound {per_unit} not reached, got {reached}")
    # A random move of length 1, for the typical case.
    g2 = torch.Generator(device="cpu")
    g2.manual_seed(1)
    rnd = torch.randn(d, d, generator=g2, dtype=torch.float64)
    rnd = rnd / rnd.norm()
    typical = float((x @ rnd).pow(2).mean().sqrt())

    res = {
        "dim": d, "n_stimuli": n,
        "weight_norm": float(w0.norm()),
        "output_rms": out_rms,
        "smax_stimuli": smax,
        "max_input_norm": xnorm,
        "worst_rms_change_per_unit_distance": per_unit,
        "typical_rms_change_per_unit_distance": typical,
        "anisotropy": per_unit / typical,
        "shipped_radius": float(R_INVARIANT),
        "worst_change_at_shipped_radius_over_output_rms": per_unit * float(R_INVARIANT) / out_rms,
        "paper1_max_drift": 0.463304,
        "worst_change_at_paper1_drift_over_output_rms": per_unit * 0.463304 / out_rms,
        "radius_for_5_percent_of_output": 0.05 * out_rms / per_unit,
        "radius_for_1_percent_of_output": 0.01 * out_rms / per_unit,
    }
    Path(a.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    for k, v in res.items():
        print(f"{k:50s} {v:.6g}" if isinstance(v, float) else f"{k:50s} {v}")


if __name__ == "__main__":
    main()
