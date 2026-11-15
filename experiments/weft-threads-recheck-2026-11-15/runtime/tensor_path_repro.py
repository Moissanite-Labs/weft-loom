#!/usr/bin/env python3
"""The tensor fast path of the Python gate accepts moves that are over the radius.

For random float32 weight pairs the exact distance is computed with rational
arithmetic. Where the float32 norm that torch returns is below the exact
distance, the radius is set between the two. The exact distance is then above
the radius, so the move must be rejected. The list path rejects it. The tensor
path accepts it.

Usage: python3 tensor_path_repro.py --weft /path/to/weft/checkout
Exit status 1 if any such accept is found (which is the defect being shown).
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from fractions import Fraction
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weft", default=os.environ.get("WEFT_CHECKOUT"))
    a = ap.parse_args()
    if not a.weft or not (Path(a.weft) / "weft" / "runtime" / "invariants" / "invariants.py").exists():
        raise SystemExit("give the weft checkout with --weft or WEFT_CHECKOUT")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(a.weft).resolve()))
    import numpy as np
    import torch
    from weft.runtime.invariants.invariants import verify_weight_update_safety_ex as gate

    rng = np.random.default_rng(20261115)
    tried = wrong = 0
    worst = 0.0
    for _ in range(400):
        n = int(rng.choice([16, 257, 4096]))
        b = rng.normal(size=n).astype(np.float32)
        c = (b + rng.normal(scale=0.05, size=n).astype(np.float32)).astype(np.float32)
        exact_sq = sum((Fraction(float(ci)) - Fraction(float(bi))) ** 2 for bi, ci in zip(b, c))
        exact = math.sqrt(exact_sq)
        d32 = float(torch.linalg.norm(torch.from_numpy(c) - torch.from_numpy(b)).item())
        if d32 >= exact:
            continue
        radius = (d32 + exact) / 2.0
        if not Fraction(radius) ** 2 < exact_sq:
            continue                                  # the radius must lie strictly below the exact distance
        tried += 1
        by_tensor = gate(torch.from_numpy(b), torch.from_numpy(c), radius, 10.0, 1.0)
        by_list = gate([float(x) for x in b], [float(x) for x in c], radius, 10.0, 1.0)
        if by_list[0]:
            raise SystemExit("FAIL: the list path accepted a move that is over the radius")
        if by_tensor[0]:
            wrong += 1
            worst = max(worst, (exact - radius) / radius)
    print(f"cases with the exact distance above the radius: {tried}")
    print(f"accepted by the tensor path: {wrong}")
    print(f"rejected by the list path: {tried}")
    print(f"largest relative excess over the radius among the accepts: {worst:.3e}")
    if wrong:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
