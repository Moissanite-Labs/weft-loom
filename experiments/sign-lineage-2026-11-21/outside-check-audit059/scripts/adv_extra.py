"""Advocate pass: two numbers the rulings quote that the other checkers do not print.

1. P2 under the other tie break at L15 rank 20/21: 28 of the pooled top-40 columns in col<512,
   exact hypergeometric tail P(X >= 28) with 1024 of 7168 columns in that block.
2. N7 over all 24 layers: 21 of 24 layers have the higher no-family share in the high block
   (counts in q08layers output), exact two-sided sign test 2 P(Bin(24, 1/2) >= 21).
3. With the optional WEM_DIR (the weight-edit files, see run_all.sh): the exact float32 value at which the L15
   ranks 20 and 21 of the per-column largest |entry| tie, as a multiple of 2^-16, and the two columns.
Exact. Run: python3 -I -B adv_extra.py [WEM_DIR]
"""
import os
import sys
from fractions import Fraction
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adv_exact as E  # noqa: E402

t = E.upper_tail_a(7168, 1024, 40, 28)
print("28/40 %.4e" % float(t))
two = Fraction(2 * sum(comb(24, j) for j in range(21, 25)), 2 ** 24)
print("21/24 two-sided %s %.4e" % (two, float(two)))
if len(sys.argv) > 1:
    import numpy as np
    W = np.asarray(np.load(os.path.join(sys.argv[1], "base_l15_down_proj_f32.npy"), allow_pickle=False), dtype=np.float32)
    linf = np.abs(W).max(axis=0)
    order = sorted(range(W.shape[1]), key=lambda c: (-float(linf[c]), c))
    v20, v21 = Fraction(float(linf[order[19]])), Fraction(float(linf[order[20]]))
    print("L15 rank 20 column %d value %s, rank 21 column %d value %s, tie %s" % (
        order[19], v20 * 65536, order[20], v21 * 65536, v20 == v21))
