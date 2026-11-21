"""Does a per-unit sign flip of (up row, down column) in a gated MLP fool the
unconstrained test phi_MATCH of Zhu, Ahmed, Kuditipudi, Liang (ICML 2025)?

Statistic as the paper defines it (arXiv 2502.12292v2, Sec. 2.3.1 eq. (4), Alg. 2, Alg. 3):
  phi_MATCH = SPEARMAN( MATCH(H_gate(t1), H_gate(t2)), MATCH(H_up(t1), H_up(t2)) )
  MATCH: C_ij = cossim(row i of W1, row j of W2); pi = LAP(C)  (code: maximize=True)
  SPEARMAN: r = 1 - 6 sum (pi1-pi2)^2 / (h(h^2-1)); t = r sqrt((h-2)/(1-r^2)); p = P(T_{h-2} > t)
Statistic as the released code computes it (github.com/ahmeda14960/model-tracing @5e65e7b,
tracing/statistics/match.py + tracing/utils/llama/matching.py, read only, not executed):
  MATCH uses squared Euclidean distances between activation rows, LAP minimize;
  p from scipy.stats.spearmanr (two-sided).
Both are computed here from my own reimplementation.

Usage: python3 -I -B zhu_signflip.py
Exit code 0 only if every exactness check passes.
"""
import sys
from fractions import Fraction
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy import stats

FAIL = []


def check(cond, msg):
    if not cond:
        FAIL.append(msg)
        print('FAIL:', msg)


# ---------------------------------------------------------------- exactness
def exact_gate(z):
    # a rational, non-odd gate (stand-in for SiLU; the symmetry never touches the gate)
    return z * (Fraction(1, 2) + z / (2 * (1 + abs(z))))


def exact_mlp(G, U, D, x):
    h = len(G)
    d_out = len(D)
    a = []
    for j in range(h):
        g = sum(G[j][k] * x[k] for k in range(len(x)))
        u = sum(U[j][k] * x[k] for k in range(len(x)))
        a.append(exact_gate(g) * u)
    return [sum(D[o][j] * a[j] for j in range(h)) for o in range(d_out)]


def exact_check(seed):
    rng = np.random.default_rng(seed)
    d, h = 3, 6
    R = lambda: Fraction(int(rng.integers(-9, 10)), int(rng.integers(1, 7)))
    G = [[R() for _ in range(d)] for _ in range(h)]
    U = [[R() for _ in range(d)] for _ in range(h)]
    D = [[R() for _ in range(h)] for _ in range(d)]
    perm = rng.permutation(h)
    s = [int(v) for v in rng.choice([-1, 1], size=h)]
    # derived: new unit j' = perm[j'] of the old, with sign s[j']
    G2 = [G[perm[j]] for j in range(h)]
    U2 = [[s[j] * v for v in U[perm[j]]] for j in range(h)]
    D2 = [[s[j] * D[o][perm[j]] for j in range(h)] for o in range(d)]
    ok = True
    for _ in range(5):
        x = [R() for _ in range(d)]
        if exact_mlp(G, U, D, x) != exact_mlp(G2, U2, D2, x):
            ok = False
    # control that must fail: flip the gate row instead of the up row
    G3 = [[s[j] * v for v in G[perm[j]]] for j in range(h)]
    U3 = [U[perm[j]] for j in range(h)]
    D3 = [[s[j] * D[o][perm[j]] for j in range(h)] for o in range(d)]
    differs = False
    for _ in range(5):
        x = [R() for _ in range(d)]
        if exact_mlp(G, U, D, x) != exact_mlp(G3, U3, D3, x):
            differs = True
    return ok, differs, s


def silu(z):
    return z / (1.0 + np.exp(-z))


def float_bitwise_check(seed):
    # sign flips only (no permutation) keep the summation order, so float64 output is bitwise equal
    rng = np.random.default_rng(seed)
    d, h, n = 16, 64, 50
    G, U, D = rng.standard_normal((h, d)), rng.standard_normal((h, d)), rng.standard_normal((d, h))
    X = rng.standard_normal((n, d))
    s = rng.choice([-1.0, 1.0], size=h)
    A = silu(X @ G.T) * (X @ U.T)
    A2 = silu(X @ G.T) * (X @ (s[:, None] * U).T)
    Y = np.stack([np.sum(A[i] * D, axis=1) for i in range(n)])
    Y2 = np.stack([np.sum(A2[i] * (D * s[None, :]), axis=1) for i in range(n)])
    return np.array_equal(Y, Y2)


# ---------------------------------------------------------------- statistic
def cos_rows(A, B):
    An = A / np.linalg.norm(A, axis=1, keepdims=True)
    Bn = B / np.linalg.norm(B, axis=1, keepdims=True)
    return An @ Bn.T


def match_paper(W1, W2, absval=False):
    C = cos_rows(W1, W2)
    if absval:
        C = np.abs(C)
    r, c = linear_sum_assignment(C, maximize=True)
    pi = np.empty(len(r), dtype=np.int64)
    pi[r] = c
    return pi


def match_code(W1, W2):
    x2 = np.sum(W1 * W1, axis=1)[:, None]
    y2 = np.sum(W2 * W2, axis=1)[None, :]
    Dm = x2 + y2 - 2 * W1 @ W2.T
    r, c = linear_sum_assignment(Dm)
    pi = np.empty(len(r), dtype=np.int64)
    pi[r] = c
    return pi


def spearman_paper(p1, p2):
    h = len(p1)
    dd = int(np.sum((p1.astype(np.int64) - p2.astype(np.int64)) ** 2))
    r = 1.0 - 6.0 * dd / (h * (h * h - 1))
    if r >= 1.0:
        return r, 0.0
    t = r * np.sqrt((h - 2) / (1 - r * r))
    return r, float(stats.t.sf(t, h - 2))


def phi_match(t1, t2, X, variant):
    G1, U1, _ = t1
    G2, U2, _ = t2
    Hg1, Hg2, Hu1, Hu2 = G1 @ X, G2 @ X, U1 @ X, U2 @ X
    if variant == 'paper':
        return spearman_paper(match_paper(Hg1, Hg2), match_paper(Hu1, Hu2))
    if variant == 'paper_abs':  # repair: sign-marginalised matching on the up branch
        return spearman_paper(match_paper(Hg1, Hg2), match_paper(Hu1, Hu2, absval=True))
    if variant == 'code':
        pg, pu = match_code(Hg1, Hg2), match_code(Hu1, Hu2)
        res = stats.spearmanr(pg, pu)
        return float(res.statistic), float(res.pvalue)
    raise ValueError(variant)


def sign_agreement(t1, t2, X):
    # our planned statistic: match by gate (sign-free), read sign of up-branch correlation
    G1, U1, _ = t1
    G2, U2, _ = t2
    pi = match_paper(G1 @ X, G2 @ X)
    c = cos_rows(U1 @ X, U2 @ X)[np.arange(len(pi)), pi]
    return float(np.mean(c > 0))


def model(rng, d, h):
    return (rng.standard_normal((h, d)) / np.sqrt(d), rng.standard_normal((h, d)) / np.sqrt(d),
            rng.standard_normal((d, h)) / np.sqrt(h))


def derive(rng, t, noise, flip_frac, d, h):
    G, U, D = t
    if noise > 0:
        G = G + noise * rng.standard_normal(G.shape) / np.sqrt(d)
        U = U + noise * rng.standard_normal(U.shape) / np.sqrt(d)
        D = D + noise * rng.standard_normal(D.shape) / np.sqrt(h)
    perm = rng.permutation(h)
    if flip_frac == 'random':
        s = rng.choice([-1.0, 1.0], size=h)
    else:
        k = int(round(flip_frac * h))
        s = np.ones(h)
        s[rng.choice(h, size=k, replace=False)] = -1.0
    return (G[perm], s[:, None] * U[perm], D[:, perm] * s[None, :])


def main():
    # exactness on rationals
    for seed in range(20):
        ok, differs, s = exact_check(1000 + seed)
        check(ok, 'exact function preservation failed, seed %d' % seed)
        check(differs, 'control (gate-row flip) did not change the function, seed %d' % seed)
    print('exact rational check: 20 seeds, up/down flip + permutation preserves output exactly;'
          ' gate-row flip control changes it:', not FAIL)
    for seed in range(10):
        check(float_bitwise_check(2000 + seed), 'float64 bitwise check failed seed %d' % seed)
    print('float64 SiLU check (signs only, same summation order): bitwise equal:', not FAIL)

    d, h, N, R = 64, 256, 1024, 60
    scen = [
        ('independent (null)', None, 0.0, 0.0),
        ('copy+perm, no flips', 'derive', 0.0, 0.0),
        ('copy+perm+random per-unit flips', 'derive', 0.0, 'random'),
        ('copy+perm+all units flipped (T6 c=-1)', 'derive', 0.0, 1.0),
        ('finetuned(0.5)+perm, no flips', 'derive', 0.5, 0.0),
        ('finetuned(0.5)+perm+random flips', 'derive', 0.5, 'random'),
        ('finetuned(0.5)+perm+all flipped', 'derive', 0.5, 1.0),
    ]
    print('\nd=%d h=%d N=%d, %d seeds per row; median r, median p, frac p<0.01' % (d, h, N, R))
    print('%-42s %-10s %8s %10s %6s | %8s' % ('scenario', 'variant', 'med r', 'med p', 'p<.01', 'signagr'))
    summary = {}
    for name, kind, noise, flip in scen:
        res = {v: [] for v in ('paper', 'code', 'paper_abs')}
        sa = []
        for k in range(R):
            rng = np.random.default_rng(10_000 * (1 + len(summary)) + k)
            t1 = model(rng, d, h)
            t2 = model(rng, d, h) if kind is None else derive(rng, t1, noise, flip, d, h)
            X = rng.standard_normal((d, N))
            for v in res:
                res[v].append(phi_match(t1, t2, X, v))
            sa.append(sign_agreement(t1, t2, X))
        for v in res:
            r = np.array([a for a, _ in res[v]])
            p = np.array([b for _, b in res[v]])
            summary[(name, v)] = (np.median(r), np.median(p), np.mean(p < 0.01))
            print('%-42s %-10s %8.3f %10.3g %6.2f | %8.3f' % (name, v, np.median(r), np.median(p),
                                                              np.mean(p < 0.01), np.median(sa)))
    # sweep flip fraction (paper variant, exact copy)
    print('\nflip-fraction sweep (exact copy + perm, paper variant): f, median r, predicted 1-f, frac p<.01')
    for f in (0.0, 0.25, 0.5, 0.75, 0.9, 0.97, 0.99, 1.0):
        rs, ps = [], []
        for k in range(30):
            rng = np.random.default_rng(777_000 + int(f * 1000) * 100 + k)
            t1 = model(rng, d, h)
            t2 = derive(rng, t1, 0.0, f, d, h)
            X = rng.standard_normal((d, N))
            r, p = phi_match(t1, t2, X, 'paper')
            rs.append(r); ps.append(p)
        print('  f=%.2f  med r=%.3f  1-f=%.3f  p<.01: %.2f' % (f, np.median(rs), 1 - f, np.mean(np.array(ps) < 0.01)))

    if FAIL:
        print('\nFAILED checks:', len(FAIL))
        sys.exit(1)
    print('\nall exactness checks passed')


if __name__ == '__main__':
    main()
