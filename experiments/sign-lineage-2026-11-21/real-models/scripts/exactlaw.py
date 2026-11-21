"""Exact null laws for the lineage instrument (PLAN.txt section d). Pure Python, integers and Fractions only.

- binomial tails of Binomial(m, 1/2)
- the cluster law of S3.2: N+ = (m + sum_j e_j |s_j|) / 2, e_j independent fair signs
- the same-position law of S4.1 for argmax matching, per-layer uniform relabelling, layers independent
"""
from fractions import Fraction
from math import comb, factorial


# ---------- binomial ----------

def binom_counts_tail_ge(m, k):
    """Integer count #{x in {0,1}^m : sum x >= k} = sum_{i>=k} C(m, i)."""
    if k <= 0:
        return 1 << m
    if k > m:
        return 0
    # sum the shorter side
    if k > m // 2:
        tot = 0
        c = comb(m, k)
        for i in range(k, m + 1):
            tot += c
            c = c * (m - i) // (i + 1)
        return tot
    # complement: 2^m - sum_{i<k}
    tot = 0
    c = 1
    for i in range(0, k):
        tot += c
        c = c * (m - i) // (i + 1)
    return (1 << m) - tot


def binom_tail_ge(m, k):
    return Fraction(binom_counts_tail_ge(m, k), 1 << m)


def binom_tail_le(m, k):
    return Fraction(binom_counts_tail_ge(m, m - k), 1 << m)  # symmetry


def two_sided(p_le, p_ge):
    p = 2 * min(p_le, p_ge)
    return p if p < 1 else Fraction(1)


def binom_test(m, k):
    """Return dict of exact one-sided upper p, lower p and two-sided p for count k of Binomial(m, 1/2)."""
    up = binom_tail_ge(m, k)
    lo = binom_tail_le(m, k)
    return {"m": m, "k": k, "p_upper": up, "p_lower": lo, "p_two": two_sided(lo, up)}


# ---------- cluster law ----------

def _group(svals):
    g = {}
    for s in svals:
        v = abs(int(s))
        if v:
            g[v] = g.get(v, 0) + 1
    return g


def cluster_cost(svals):
    g = _group(svals)
    if not g:
        return 0
    vstar = max(g, key=lambda v: (g[v], -v))
    width = 1
    cost = 0
    for v in sorted(g):
        if v == vstar:
            continue
        cost += width * (g[v] + 1)
        width += 2 * v * g[v]
    return cost


def cluster_counts(svals):
    """Exact law of S = sum_j e_j |s_j| as (J, vstar, cstar, D) where the full count of sign vectors with S = s is
    sum over s' of D[s'] * #{B : vstar (2B - cstar) = s - s'}, B ~ the count of +1 among the cstar largest-group signs.
    D is a dict s' -> integer count over the other groups' sign vectors."""
    g = _group(svals)
    J = sum(g.values())
    if not g:
        return J, 1, 0, {0: 1}
    vstar = max(g, key=lambda v: (g[v], -v))
    cstar = g[vstar]
    D = {0: 1}
    for v in sorted(g):
        if v == vstar:
            continue
        c = g[v]
        coefs = [comb(c, k) for k in range(c + 1)]
        nd = {}
        for s, cnt in D.items():
            for k in range(c + 1):
                key = s + v * (2 * k - c)
                nd[key] = nd.get(key, 0) + cnt * coefs[k]
        D = nd
    return J, vstar, cstar, D


def _ceil_div(a, b):
    return -((-a) // b)


def cluster_test(svals, m, nplus, cap=2 * 10 ** 8):
    """Exact P(N+ >= nplus), P(N+ <= nplus), two-sided, under the cluster law. svals: the s_j of every target cluster
    (zeros allowed). m: number of kept pairs (= sum of cluster sizes). Returns dict; if the exact convolution would
    exceed `cap` multiply-adds, returns the Hoeffding bounds instead with 'exact': False."""
    svals = [int(s) for s in svals]
    sum_abs = sum(abs(s) for s in svals)
    # N+ = (m + S)/2 with S = sum e_j |s_j|; the observed S is 2 nplus - m
    t = 2 * nplus - m
    if (m - sum_abs) % 2:
        raise ValueError("parity: m and sum|s_j| must agree mod 2")
    cost = cluster_cost(svals)
    if cost > cap:
        v = sum(s * s for s in svals)
        import math
        up = 1.0 if t <= 0 else math.exp(-t * t / (2.0 * v))
        lo = 1.0 if t >= 0 else math.exp(-t * t / (2.0 * v))
        return {"exact": False, "cost": cost, "hoeffding_upper": up, "hoeffding_lower": lo,
                "hoeffding_two": min(1.0, 2 * min(up, lo)), "var_S": v}
    J, vstar, cstar, D = cluster_counts(svals)
    # tails of B ~ Bin(cstar): T_ge[k] = #{B >= k}
    tge = [0] * (cstar + 2)
    c = 1
    row = []
    for k in range(cstar + 1):
        row.append(c)
        c = c * (cstar - k) // (k + 1)
    acc = 0
    for k in range(cstar, -1, -1):
        acc += row[k]
        tge[k] = acc

    def count_ge(u):  # #{B : vstar (2B - cstar) >= u}
        # vstar(2B - cstar) >= u  <=>  2B >= u/vstar + cstar  <=> B >= ceil((ceil(u/vstar) + cstar)/2)
        k = _ceil_div(_ceil_div(u, vstar) + cstar, 2)
        if k <= 0:
            return 1 << cstar
        if k > cstar:
            return 0
        return tge[k]

    def count_le(u):  # #{B : vstar (2B - cstar) <= u}
        # complement of >= u+1
        return (1 << cstar) - count_ge(u + 1)

    n_ge = sum(cnt * count_ge(t - s) for s, cnt in D.items())
    n_le = sum(cnt * count_le(t - s) for s, cnt in D.items())
    den = 1 << J
    up = Fraction(n_ge, den)
    lo = Fraction(n_le, den)
    return {"exact": True, "cost": cost, "p_upper": up, "p_lower": lo, "p_two": two_sided(lo, up),
            "var_S": sum(s * s for s in svals)}


# ---------- same position ----------

def falling(N, r):
    out = 1
    for i in range(r):
        out *= N - i
    return out


def elem_sym_trunc(ns, K):
    """e_0..e_K of the multiset ns (integers), exact."""
    e = [1] + [0] * K
    top = 0
    for n in ns:
        top = min(top + 1, K)
        for r in range(top, 0, -1):
            e[r] += n * e[r - 1]
    return e


def same_position_moments(layers, K):
    """layers: list of (N_L, [n_j for target units j of layer L with n_j > 0]). Returns factorial moments
    M_0..M_K of F = sum_L F_L (Fractions), and R = the largest r with M_r possibly nonzero."""
    total = [Fraction(1)] + [Fraction(0)] * K
    R = 0
    for N, ns in layers:
        ns = [int(n) for n in ns if n > 0]
        RL = min(len(ns), N)
        R += RL
        e = elem_sym_trunc(ns, min(K, RL))
        G = [Fraction(e[r], falling(N, r)) for r in range(len(e))]
        new = [Fraction(0)] * (K + 1)
        for a, ta in enumerate(total):
            if ta == 0:
                continue
            for b, gb in enumerate(G):
                if a + b > K:
                    break
                new[a + b] += ta * gb
        total = new
    return total, R


def same_position_test(layers, k, extra=40, kmax=300):
    """P(F >= k) under per-layer uniform relabelling. Exact when the series ends within the truncation; otherwise a
    rigorous Bonferroni bracket [lo, hi]. Above kmax: the bound L^k / k! (L = number of layers). Also the exact mean."""
    mean = sum((Fraction(sum(int(n) for n in ns), N) for N, ns in layers), Fraction(0))
    L = len(layers)
    if k <= 0:
        return {"k": k, "mean": mean, "exact": True, "p_upper": Fraction(1)}
    if k > kmax:
        b = Fraction(L ** k, factorial(k))
        return {"k": k, "mean": mean, "exact": False, "bound_upper": b, "bound_kind": "L^k/k!"}
    K = max(k + extra, 2)
    M, R = same_position_moments(layers, K)
    if k > R:
        return {"k": k, "mean": mean, "exact": True, "p_upper": Fraction(0)}
    top = min(K, R)
    partial = []
    s = Fraction(0)
    for r in range(k, top + 1):
        term = comb(r - 1, k - 1) * M[r]
        s = s + term if (r - k) % 2 == 0 else s - term
        partial.append(s)
    if top == R:
        return {"k": k, "mean": mean, "exact": True, "p_upper": partial[-1]}
    if len(partial) == 1:  # first Bonferroni term alone is an upper bound
        lo, hi = Fraction(0), partial[0]
    else:
        lo = min(partial[-1], partial[-2])
        hi = max(partial[-1], partial[-2])
    out = {"k": k, "mean": mean, "exact": False, "bracket": (max(lo, Fraction(0)), min(hi, Fraction(1)))}
    # Cantelli (one-sided Chebyshev) lower bound on P(F >= k) when k - 1 < mean, from the exact variance
    var = 2 * M[2] + M[1] - M[1] * M[1]
    gap = mean - (k - 1)
    if gap > 0:
        cl = 1 - var / (var + gap * gap)
        if cl > out["bracket"][0]:
            out["bracket"] = (cl, out["bracket"][1])
            out["lower_from"] = "cantelli"
    return out


def same_position_law_exact(layers):
    """Full law P(F = k), k = 0..R (only for small cases; used by the checker)."""
    M, R = same_position_moments(layers, sum(min(len([n for n in ns if n > 0]), N) for N, ns in layers))
    law = []
    for k in range(R + 1):
        p = Fraction(0)
        for r in range(k, R + 1):
            term = comb(r, k) * M[r]
            p = p + term if (r - k) % 2 == 0 else p - term
        law.append(p)
    return law
