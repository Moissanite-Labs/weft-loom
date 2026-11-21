"""Advocate pass: exact hypergeometric tails by two unrelated routes, plus a stratified sum.

Route A: sum of integer binomial products over comb(N, n).
Route B: point probabilities built by a Fraction ratio recursion from P(X = 0), complement taken.
Routes share no arithmetic beyond Python integers. No bare assert.
"""
from fractions import Fraction
from math import comb


class ExactError(Exception):
    pass


def upper_tail_a(N, K, n, k):
    hi = min(K, n)
    if k > hi:
        return Fraction(0)
    lo = max(0, n - (N - K))
    k = max(k, lo)
    return Fraction(sum(comb(K, j) * comb(N - K, n - j) for j in range(k, hi + 1)), comb(N, n))


def pmf_b(N, K, n):
    lo = max(0, n - (N - K))
    hi = min(K, n)
    # P(X = lo) by a product of ratios, then the ratio recursion upward.
    p = Fraction(1)
    # P(X=lo) = C(K,lo) C(N-K,n-lo) / C(N,n), written as products.
    for i in range(lo):
        p *= Fraction(K - i, i + 1)
    for i in range(n - lo):
        p *= Fraction(N - K - i, i + 1)
    for i in range(n):
        p *= Fraction(i + 1, N - i)
    out = {lo: p}
    for j in range(lo, hi):
        p = p * Fraction((K - j) * (n - j), (j + 1) * (N - K - n + j + 1))
        out[j + 1] = p
    return out


def upper_tail_b(N, K, n, k):
    pm = pmf_b(N, K, n)
    total = sum(pm.values())
    if total != 1:
        raise ExactError("route B pmf does not sum to 1")
    below = sum(v for j, v in pm.items() if j < k)
    return 1 - below


def lower_tail(N, K, n, k):
    pm = pmf_b(N, K, n)
    return sum(v for j, v in pm.items() if j <= k)


def tail_checked(N, K, n, k):
    a = upper_tail_a(N, K, n, k)
    b = upper_tail_b(N, K, n, k)
    if a != b:
        raise ExactError("routes disagree for %r" % ((N, K, n, k),))
    return a


def stratified_upper_tail(strata, observed_total):
    """strata = [(N, K, n), ...]; exact P(sum X_s >= observed_total), X_s independent."""
    dist = {0: Fraction(1)}
    for (N, K, n) in strata:
        pm = pmf_b(N, K, n)
        nd = {}
        for s, ps in dist.items():
            for j, pj in pm.items():
                nd[s + j] = nd.get(s + j, Fraction(0)) + ps * pj
        dist = nd
    return sum(v for s, v in dist.items() if s >= observed_total)


def binom_two_sided_half(n, k):
    m = min(k, n - k)
    t = Fraction(2 * sum(comb(n, j) for j in range(m + 1)), 2 ** n)
    return min(t, Fraction(1))


def sci(fr):
    """Float text for a Fraction, for printing only."""
    return "%.4e" % float(fr)
