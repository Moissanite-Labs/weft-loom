"""Exact null laws for the neuron-sign lineage test and the same-position count.

Integers and fractions.Fraction only. No floats on any exact path.
Run: python3 -I -B exact_null.py   (also -I -O -B and -I -B -W error)
It runs its self-tests and writes ../out/exact_cases.json for the independent
checker (check_independent.py), which shares no code with this file.

Definitions (the statements S3 and S4 summarised in the README).
  Pairs: A unit i is matched to B unit m(i); c_i = sign of corr(a_i, b_m(i)).
  s_j = #{i: m(i)=j, c_i=+1} - #{i: m(i)=j, c_i=-1}.
  N+ = number of positive pairs = (m + sum_j s_j)/2.
  Null law given A and the sign-orbit of B: N+ = (m + sum_j e_j |s_j|)/2, e_j iid fair signs.
"""
import json
import os
import sys


def _opt(name, default):
    """Folder option from the command line (for example --out DIR), with the record's layout as default."""
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument(name, default=default)
    known, rest = ap.parse_known_args()
    sys.argv[1:] = rest
    return getattr(known, name.lstrip("-").replace("-", "_"))
from fractions import Fraction
from math import comb, factorial


class CheckFailure(Exception):
    pass


def require(cond, msg):
    if not cond:
        raise CheckFailure(msg)


# ---------------------------------------------------------------- binomial

def binom_upper(m, k):
    """P(Bin(m,1/2) >= k) exactly."""
    if k <= 0:
        return Fraction(1)
    if k > m:
        return Fraction(0)
    return Fraction(sum(comb(m, x) for x in range(k, m + 1)), 2 ** m)


def binom_lower(m, k):
    """P(Bin(m,1/2) <= k) exactly."""
    if k < 0:
        return Fraction(0)
    if k >= m:
        return Fraction(1)
    return Fraction(sum(comb(m, x) for x in range(0, k + 1)), 2 ** m)


def binom_two_sided(m, k):
    """P(|Bin - m/2| >= |k - m/2|) exactly."""
    dev2 = abs(2 * k - m)
    tot = sum(comb(m, x) for x in range(m + 1) if abs(2 * x - m) >= dev2)
    return Fraction(tot, 2 ** m)


# ---------------------------------------------------------------- cluster law

def cluster_s(matches, signs):
    """matches: list of B indices (one per A unit kept); signs: list of +1/-1.
    Returns dict j -> s_j and the observed N+."""
    require(len(matches) == len(signs), "length mismatch")
    s = {}
    npos = 0
    for j, c in zip(matches, signs):
        require(c in (1, -1), "sign must be +1 or -1")
        s[j] = s.get(j, 0) + c
        if c == 1:
            npos += 1
    return s, npos


def cluster_sum_counts(abs_s):
    """Integer counts of S = sum_j e_j*v_j over all 2^J sign vectors.
    Returns (offset, counts, J) with counts[t] = #{e : S = t - offset}."""
    groups = {}
    for v in abs_s:
        require(isinstance(v, int) and v >= 0, "abs_s must be non-negative ints")
        groups[v] = groups.get(v, 0) + 1
    total = sum(v * k for v, k in groups.items())
    offset = total
    counts = [0] * (2 * total + 1)
    counts[offset] = 1
    J = 0
    for v, k in sorted(groups.items()):
        J += k
        if v == 0:
            # each zero-valued unit doubles every count
            counts = [c * (2 ** k) for c in counts]
            continue
        new = [0] * len(counts)
        coeffs = [comb(k, x) for x in range(k + 1)]
        for t, c in enumerate(counts):
            if c == 0:
                continue
            for x in range(k + 1):
                u = t + v * (2 * x - k)
                new[u] += c * coeffs[x]
        counts = new
    require(sum(counts) == 2 ** J, "counts do not sum to 2^J")
    return offset, counts, J


def cluster_law_npos(abs_s, m):
    """Exact law of N+ = (m + S)/2 as dict n -> Fraction."""
    offset, counts, J = cluster_sum_counts(abs_s)
    den = 2 ** J
    law = {}
    for t, c in enumerate(counts):
        if c == 0:
            continue
        S = t - offset
        require((m + S) % 2 == 0, "parity violation: m + S must be even")
        law[(m + S) // 2] = Fraction(c, den)
    return law


def cluster_pvalues(matches, signs):
    """Exact one-sided upper, lower and two-sided p-values of the observed N+
    under the cluster null. Returns dict of Fractions plus summary integers."""
    s, npos = cluster_s(matches, signs)
    m = len(matches)
    abs_s = [abs(v) for v in s.values()]
    offset, counts, J = cluster_sum_counts(abs_s)
    den = 2 ** J
    s_obs = 2 * npos - m
    up = sum(c for t, c in enumerate(counts) if t - offset >= s_obs)
    lo = sum(c for t, c in enumerate(counts) if t - offset <= s_obs)
    two = sum(c for t, c in enumerate(counts) if abs(t - offset) >= abs(s_obs))
    return {
        "m": m, "npos": npos, "J": J,
        "sum_s2": sum(v * v for v in abs_s),
        "p_upper": Fraction(up, den), "p_lower": Fraction(lo, den),
        "p_two": Fraction(two, den),
    }


# ---------------------------------------------------------------- same position

def elementary_symmetric(ns, kmax):
    """e_0..e_kmax of the integers ns, by integer DP."""
    e = [1] + [0] * kmax
    for n in ns:
        for k in range(kmax, 0, -1):
            e[k] += e[k - 1] * n
    return e


def same_position_law(class_sizes, N):
    """Exact law of F = #{A positions i : pi(m(i)) = i} when B's N units are
    relabelled by a uniform random permutation pi, given that the A positions
    matched to B unit j form a set S_j of size n_j (sets disjoint, positions
    in 1..N). class_sizes = [n_j]. Rook-polynomial inclusion-exclusion.
    Returns list P(F=k) for k=0..K as Fractions, K = number of nonzero classes."""
    ns = [n for n in class_sizes if n > 0]
    require(sum(ns) <= N, "more matched positions than B units")
    K = len(ns)
    r = elementary_symmetric(ns, K)
    nf = factorial(N)
    law = []
    for k in range(K + 1):
        tot = 0
        for rr in range(k, K + 1):
            term = comb(rr, k) * r[rr] * factorial(N - rr)
            tot += term if (rr - k) % 2 == 0 else -term
        require(tot >= 0, "negative count in inclusion-exclusion")
        law.append(Fraction(tot, nf))
    require(sum(law) == 1, "same-position law does not sum to 1")
    return law


def fixed_point_law(N):
    """Fixed points of a uniform permutation of N: the bijection case."""
    return same_position_law([1] * N, N)


def tail_upper(law, k):
    return sum((p for i, p in enumerate(law) if i >= k), Fraction(0))


# ---------------------------------------------------------------- self tests

def lcg(seed):
    x = seed
    while True:
        x = (6364136223846793005 * x + 1442695040888963407) % (2 ** 64)
        yield x >> 33


def selftest():
    results = {}
    # T1: one-to-one matching gives Binomial(m,1/2)
    for m in (1, 5, 12, 40):
        law = cluster_law_npos([1] * m, m)
        for k in range(m + 1):
            require(law.get(k, Fraction(0)) == Fraction(comb(m, k), 2 ** m),
                    "T1 one-to-one cluster law != binomial at m=%d k=%d" % (m, k))
    results["T1_one_to_one_is_binomial"] = "pass"
    # T2: mean m/2 and variance sum s^2/4 exactly, for random clusterings
    g = lcg(20261121)
    for trial in range(30):
        J = 1 + next(g) % 9
        abs_s = [next(g) % 5 for _ in range(J)]
        m = sum(abs_s) + 2 * (next(g) % 3)  # m >= sum|s|, same parity
        law = cluster_law_npos(abs_s, m)
        mean = sum(Fraction(n) * p for n, p in law.items())
        var = sum((Fraction(n) - mean) ** 2 * p for n, p in law.items())
        require(mean == Fraction(m, 2), "T2 mean != m/2")
        require(var == Fraction(sum(v * v for v in abs_s), 4), "T2 var != sum s^2 / 4")
    results["T2_mean_and_variance"] = "pass"
    # T3: fixed-point law of uniform permutation: mean 1, variance 1 (N>=2)
    for N in (2, 3, 7, 15):
        law = fixed_point_law(N)
        mean = sum(k * p for k, p in enumerate(law))
        var = sum((k - mean) ** 2 * p for k, p in enumerate(law))
        require(mean == 1 and var == 1, "T3 fixed points mean/var at N=%d" % N)
    results["T3_fixed_points_mean_var_1"] = "pass"
    # T4: general argmax classes: mean = (#matched positions)/N and P(F>=k) <= 1/k!
    for trial in range(30):
        N = 2 + next(g) % 10
        J = 1 + next(g) % N
        ns = [0] * J
        for _ in range(N):
            ns[next(g) % J] += 1
        law = same_position_law(ns, N)
        mean = sum(k * p for k, p in enumerate(law))
        require(mean == Fraction(sum(ns), N), "T4 mean")
        for k in range(len(law)):
            require(tail_upper(law, k) <= Fraction(1, factorial(k)), "T4 1/k! bound")
    results["T4_argmax_classes_mean_and_bound"] = "pass"
    # Must-fail control: a wrong law (binomial) for a clustered case must differ.
    law = cluster_law_npos([3, 1], 4)
    require(law != {k: Fraction(comb(4, k), 16) for k in range(5)},
            "control: clustered law unexpectedly equals binomial")
    results["C1_clustered_law_differs_from_binomial"] = "pass (differs, as it must)"
    return results


def export_cases():
    """Cases for the independent checker: inputs and exact outputs as strings."""
    g = lcg(777)
    cases = []
    for trial in range(25):
        J = 1 + next(g) % 8
        matches, signs = [], []
        for i in range(4 + next(g) % 12):
            matches.append(next(g) % J)
            signs.append(1 if next(g) % 2 else -1)
        pv = cluster_pvalues(matches, signs)
        cases.append({"kind": "cluster", "matches": matches, "signs": signs,
                      "p_upper": str(pv["p_upper"]), "p_lower": str(pv["p_lower"]),
                      "p_two": str(pv["p_two"])})
    for trial in range(15):
        N = 2 + next(g) % 7
        J = 1 + next(g) % N
        ns = [0] * J
        for _ in range(N - next(g) % 2):
            ns[next(g) % J] += 1
        law = same_position_law(ns, N)
        cases.append({"kind": "same_position", "class_sizes": ns, "N": N,
                      "law": [str(p) for p in law]})
    for (m, k) in [(200, 66), (200, 118), (256, 140), (1000, 330)]:
        cases.append({"kind": "binomial", "m": m, "k": k,
                      "upper": str(binom_upper(m, k)), "lower": str(binom_lower(m, k))})
    return cases


def main():
    res = selftest()
    here = os.path.dirname(os.path.abspath(__file__))
    out = _opt("--out", os.path.join(here, "..", "out"))
    os.makedirs(out, exist_ok=True)
    cases = export_cases()
    with open(os.path.join(out, "exact_cases.json"), "w", newline="\n") as f:
        json.dump({"selftest": res, "cases": cases}, f, indent=1, sort_keys=True)
    print(json.dumps(res, sort_keys=True))
    print("cases exported:", len(cases))


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as e:
        print("CHECK FAILED:", e)
        sys.exit(1)
