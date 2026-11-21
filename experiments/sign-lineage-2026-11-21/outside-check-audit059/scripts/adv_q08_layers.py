"""Advocate pass: N7 (21/21 sign test window) and N4 (2^-16 grid) checks.

argv[1] q08 page (read only), argv[2] dir with base_l{15,19}_down_proj_f32.npy.
N7: all 24 layers; per layer the exact chance, under within-layer exchangeability of the
no-family labels over columns [0,512) U [2048,3584) (conditional on their count), that the
high block's share exceeds the low block's; product over layers = exact chance of the joint
event; plus per-layer exact one-sided tails. Exact Fractions throughout. No bare assert.
"""
import os
import sys
from fractions import Fraction
from math import comb

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adv_exact as ex  # noqa: E402
import adv_page as pg  # noqa: E402


def p_hi_gt_lo(K, n_lo=512, n_hi=1536):
    """X = no-family count in the high block, X ~ HG(n_lo+n_hi, K, n_hi).
    hi share > lo share  <=>  X/n_hi > (K-X)/n_lo  <=>  X*n_lo > (K-X)*n_hi."""
    N = n_lo + n_hi
    tot = 0
    for x in range(max(0, K - n_lo), min(K, n_hi) + 1):
        if x * n_lo > (K - x) * n_hi:
            tot += comb(K, x) * comb(N - K, n_hi - x)
    return Fraction(tot, comb(N, n_hi))


def main(page, wdir):
    d = pg.load_data(page)
    ids = pg.group_ids(d)
    fam = pg.family_of_neuron(d, ids)
    W, L = int(d["width"]), int(d["layers"])
    joint_mid = Fraction(1)
    joint_all = Fraction(1)
    n_mid = n_all = 0
    min_tail = None
    for lay in range(L):
        b = lay * W
        lo = sum(1 for c in range(0, 512) if fam[b + c] < 0)
        hi = sum(1 for c in range(2048, W) if fam[b + c] < 0)
        K = lo + hi
        gt = hi * 512 > lo * 1536
        q = p_hi_gt_lo(K)
        tail = ex.tail_checked(2048, K, 1536, hi)
        print("L%02d lo %3d/512 hi %3d/1536 hi>lo %-5s P_null(hi>lo)=%.4f exact one-sided tail %s" % (
            lay, lo, hi, gt, float(q), ex.sci(tail)))
        if gt:
            n_all += 1
            joint_all *= q
            if 2 <= lay <= 22:
                n_mid += 1
                joint_mid *= q
        if 2 <= lay <= 22:
            min_tail = tail if min_tail is None else max(min_tail, tail)
    print("hi>lo in %d of 24 layers; in %d of 21 layers L02..L22" % (n_all, n_mid))
    print("exact null chance of hi>lo in all 21 of L02..L22 (product, conditional on counts): %s" % ex.sci(joint_mid))
    print("largest per-layer one-sided tail among L02..L22: %s" % ex.sci(min_tail))
    print("their sign-test value 2^-20 = %s" % ex.sci(ex.binom_two_sided_half(21, 21)))

    # N4: share of entries off the 2^-16 grid, and of bf16 origin.
    for layer in (15, 19):
        Wt = np.load(os.path.join(wdir, "base_l%d_down_proj_f32.npy" % layer), allow_pickle=False)
        bits = Wt.astype(np.float32).view(np.uint32)
        bf16 = float(((bits & 0xFFFF) == 0).mean())
        x = Wt.astype(np.float64) * 65536.0
        off = float((x != np.round(x)).mean())
        small = float((np.abs(Wt) < 2.0 ** -9).mean())
        print("L%d: bf16-exact entries %.4f; entries off the 2^-16 grid %.4f; |w| < 2^-9: %.4f" % (
            layer, bf16, off, small))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
