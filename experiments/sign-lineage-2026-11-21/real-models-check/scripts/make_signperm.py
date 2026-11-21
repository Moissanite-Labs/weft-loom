"""My own laundering spec (seed differs from the first agent's 777).

Per MLP layer: an independent uniform permutation of the hidden units and an independent fair sign per unit,
from numpy.random.Generator(PCG64(seed)). Laundered unit k (global order) = sign[k] * original unit perm[k],
perm[k] in the same layer as k. In weights: gate row k <- gate row perm[k]; up row k <- sign[k] * up row
perm[k]; down column k <- sign[k] * down column perm[k].

Usage: python -I make_signperm.py <layers> <width> <seed> <out.npz>
"""
import sys
import numpy as np


def main():
    L, h, seed, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    g = np.random.Generator(np.random.PCG64(seed))
    perm = np.empty(L * h, dtype=np.int64)
    sign = np.empty(L * h, dtype=np.int64)
    for l in range(L):
        perm[l * h:(l + 1) * h] = g.permutation(h) + l * h
        sign[l * h:(l + 1) * h] = np.where(g.integers(0, 2, size=h) == 1, 1, -1)
    np.savez(out, perm=perm, sign=sign, seed=seed, layers=L, width=h)
    print("fixed points", int((perm == np.arange(L * h)).sum()), "negated", int((sign < 0).sum()), "of", L * h)


if __name__ == "__main__":
    main()
