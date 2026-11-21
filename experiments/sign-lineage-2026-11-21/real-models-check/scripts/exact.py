"""Exact null laws, pure Python integers and fractions.Fraction (second checker; shares no code with
real-models/scripts/exactlaw.py, which was not read before these numbers existed).

  binom_tails(m, k)        -> (P(X <= k), P(X >= k)) for X ~ Binomial(m, 1/2), exact Fractions
  binom_two_sided(m, k)    -> min(1, 2 min(lower, upper))
  cluster_tails(hist, s)   -> (P(S <= s), P(S >= s)) for S = sum_j e_j a_j, e_j fair signs, a_j from hist {a: count}
  same_pos_upper(layers, k, extra=80)
                           -> (lo, hi) rigorous bracket of P(F >= k), F = sum over layers of the rook-law count;
                              layers = [(N, {n: count}), ...]; per-layer pmf by inclusion-exclusion with
                              Bonferroni partial sums, then convolution of lower and of upper bounds.
  same_pos_mean(layers)    -> exact mean sum n_j / N
  factorial_bound_small(L, k) -> True when L^k / k! < 1/1000 (exact integer comparison)
"""
from fractions import Fraction
from math import comb


def binom_lower_sum(m, k):
    """sum_{i=0}^{k} C(m, i) as an integer (k may be < 0)."""
    if k < 0:
        return 0
    if k >= m:
        return 1 << m
    if k > m // 2:
        return (1 << m) - binom_lower_sum(m, m - k - 1)
    total = 0
    c = 1
    for i in range(0, k + 1):
        total += c
        c = c * (m - i) // (i + 1)
    return total


def binom_tails(m, k):
    den = 1 << m
    lower = Fraction(binom_lower_sum(m, k), den)
    upper = Fraction(den - binom_lower_sum(m, k - 1), den)
    return lower, upper


def binom_two_sided(m, k):
    lo, up = binom_tails(m, k)
    return min(Fraction(1), 2 * min(lo, up))


def cluster_dist(hist):
    """Exact law of S = sum e_j a_j as (offset, list of integer weights, denominator exponent)."""
    items = sorted(((int(a), int(c)) for a, c in hist.items() if int(a) != 0 and int(c) != 0))
    # distribution over values v in [-M, M]; stored as list indexed by v + M; integer weights
    total = sum(a * c for a, c in items)
    w = [0] * (2 * total + 1)
    w[total] = 1
    lo_v, hi_v = 0, 0  # current support range
    for a, c in items:
        new = [0] * (2 * total + 1)
        coeffs = [comb(c, b) for b in range(c + 1)]
        for v in range(lo_v, hi_v + 1):
            x = w[v + total]
            if x == 0:
                continue
            for b in range(c + 1):
                new[v + a * (2 * b - c) + total] += x * coeffs[b]
        w = new
        lo_v -= a * c
        hi_v += a * c
    nexp = sum(c for a, c in items)
    return total, w, nexp


def cluster_tails(hist, s_obs):
    total, w, nexp = cluster_dist(hist)
    den = 1 << nexp
    le = sum(w[:max(0, min(len(w), s_obs + total + 1))])
    ge = sum(w[max(0, s_obs + total):])
    return Fraction(le, den), Fraction(ge, den)


def esym_from_hist(nhist, R):
    """e_r(n) for r = 0..R where n is the multiset {n: count}; prod_a (1 + a x)^c truncated at degree R."""
    poly = [1] + [0] * R
    for a, c in sorted((int(a), int(c)) for a, c in nhist.items()):
        fac = [comb(c, t) * a ** t for t in range(min(c, R) + 1)]
        new = [0] * (R + 1)
        for i, x in enumerate(poly):
            if x == 0:
                continue
            for t, y in enumerate(fac):
                if i + t > R:
                    break
                new[i + t] += x * y
        poly = new
    return poly


def falling(N, r):
    out = 1
    for t in range(r):
        out *= (N - t)
    return out


def layer_pmf_bracket(N, nhist, jmax, extra):
    """Bracket of P(F_L = j), j = 0..jmax, as lists (lo, hi) of Fractions, via truncated inclusion-exclusion.

    Partial sum to r = j + t is an upper bound for t even and a lower bound for t odd (Bonferroni).
    When R reaches the polynomial degree the sum is exact.
    """
    deg = sum(int(c) for a, c in nhist.items() if int(a) > 0)
    R = min(deg, jmax + extra)
    e = esym_from_hist(nhist, R)
    M = [Fraction(e[r], falling(N, r)) for r in range(R + 1)]
    lo, hi = [], []
    for j in range(jmax + 1):
        if j > R:
            lo.append(Fraction(0)); hi.append(Fraction(0) if R == deg else Fraction(1))
            continue
        part = Fraction(0)
        last_even = None; last_odd = None
        for r in range(j, R + 1):
            term = comb(r, j) * M[r]
            part = part + term if (r - j) % 2 == 0 else part - term
            if (r - j) % 2 == 0:
                last_even = part
            else:
                last_odd = part
        if R == deg:
            l = h = part
        else:
            h = last_even
            l = last_odd if last_odd is not None else Fraction(0)
        lo.append(max(Fraction(0), l)); hi.append(min(Fraction(1), h))
    return lo, hi


def convolve(p, q, kmax):
    out = [Fraction(0)] * (kmax + 1)
    for i, x in enumerate(p):
        if i > kmax or x == 0:
            continue
        for j, y in enumerate(q):
            if i + j > kmax:
                break
            out[i + j] += x * y
    return out


def same_pos_upper(layers, k, extra=80):
    if k <= 0:
        return Fraction(1), Fraction(1)
    jmax = k - 1
    tot_lo = [Fraction(1)] + [Fraction(0)] * jmax
    tot_hi = [Fraction(1)] + [Fraction(0)] * jmax
    for N, nhist in layers:
        lo, hi = layer_pmf_bracket(int(N), nhist, jmax, extra)
        tot_lo = convolve(tot_lo, lo, jmax)
        tot_hi = convolve(tot_hi, hi, jmax)
    p_lo = 1 - sum(tot_hi)
    p_hi = 1 - sum(tot_lo)
    return max(Fraction(0), p_lo), min(Fraction(1), p_hi)


def same_pos_mean(layers):
    return sum((Fraction(sum(int(a) * int(c) for a, c in nh.items()), int(N)) for N, nh in layers), Fraction(0))


def same_pos_variance(layers):
    """Exact variance: sum over layers of (2 M2 + M1 - M1^2), M_r the factorial moments."""
    v = Fraction(0)
    for N, nh in layers:
        e = esym_from_hist(nh, 2)
        M1 = Fraction(e[1], int(N))
        M2 = Fraction(e[2], falling(int(N), 2)) if int(N) >= 2 else Fraction(0)
        v += 2 * M2 + M1 - M1 * M1
    return v


def factorial_bound_small(L, k):
    """Exact test of L^k / k! < 1/1000; returns (bool, log10 of the bound)."""
    from math import lgamma, log10, log
    fk = 1
    for t in range(2, k + 1):
        fk *= t
    ok = 1000 * (L ** k) < fk
    return ok, (k * log10(L) - lgamma(k + 1) / log(10))


def log10_fraction(x):
    """log10 of a positive Fraction, safe for huge or tiny values."""
    from math import log10
    if x <= 0:
        return float("-inf")
    return log10(x.numerator) - log10(x.denominator)


def fmt(x):
    if x == 0:
        return "0"
    l = log10_fraction(x)
    if l > -300:
        return "%.6e" % float(x)
    e = int(l // 1)
    return "%.3fe%d" % (10 ** (l - e), e)
