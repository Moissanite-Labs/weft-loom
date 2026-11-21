"""Independent exact checks of S3 and S4 (refuter's own code, shares nothing with ../scripts).

Pure Python, Fraction / int arithmetic only. No assert on a checking path: failures are
counted and printed, exit code 1 if any check that is expected to pass fails.

Run:  python3 -I -B exact_refute.py ; python3 -I -O -B exact_refute.py ; python3 -I -B -W error exact_refute.py
"""
import itertools
import random
import sys
from fractions import Fraction
from math import comb, factorial

FAIL = []
NOTE = []


def check(name, ok, detail=""):
    if not ok:
        FAIL.append((name, detail))
    return ok


# ---------------------------------------------------------------- matching primitives
def sgn(x):
    return (x > 0) - (x < 0)


def argmax_abs(row):
    """first index of max |value| (tie rule depends on |.| and index only)"""
    best, bj = None, None
    for j, v in enumerate(row):
        a = abs(v)
        if best is None or a > best:
            best, bj = a, j
    return bj


def site_stat(C, tau):
    """C[i][j] = corr(a_i, b_j). returns (m, Nplus, Nzero, match list)"""
    m = 0
    nplus = 0
    nzero = 0
    match = []
    for i, row in enumerate(C):
        j = argmax_abs(row)
        if abs(row[j]) >= tau:
            m += 1
            s = sgn(row[j])
            nplus += s > 0
            nzero += s == 0
            match.append((i, j, s))
    return m, nplus, nzero, match


def flip_cols(C, e):
    return [[v * e[j] for j, v in enumerate(row)] for row in C]


def flip_rows(C, d):
    return [[v * d[i] for v in row] for i, row in enumerate(C)]


# ---------------------------------------------------------------- my own cluster law (S3.2)
def cluster_law(match):
    """law of N+ under fair independent signs on target units, from formula
    N+ = (m + sum_j e_j |s_j|)/2. Returns dict N+ -> Fraction."""
    s = {}
    m = 0
    for (_, j, c) in match:
        m += 1
        s[j] = s.get(j, 0) + c
    # distribution of sum e_j |s_j| as dict
    dist = {0: 1}
    for j, sj in s.items():
        a = abs(sj)
        nd = {}
        for k, w in dist.items():
            nd[k + a] = nd.get(k + a, 0) + w
            nd[k - a] = nd.get(k - a, 0) + w
        dist = nd
    tot = sum(dist.values())
    out = {}
    for k, w in dist.items():
        num = m + k
        if num % 2:
            return None  # formula gives a half-integer: formula invalid here
        out[num // 2] = out.get(num // 2, 0) + Fraction(w, tot)
    return out


def brute_law_target(C, tau):
    nB = len(C[0])
    law = {}
    for e in itertools.product((1, -1), repeat=nB):
        _, npl, _, _ = site_stat(flip_cols(C, e), tau)
        law[npl] = law.get(npl, 0) + Fraction(1, 2 ** nB)
    return law


def brute_law_source(C, tau):
    nA = len(C)
    law = {}
    for d in itertools.product((1, -1), repeat=nA):
        _, npl, _, _ = site_stat(flip_rows(C, d), tau)
        law[npl] = law.get(npl, 0) + Fraction(1, 2 ** nA)
    return law


def binom_law(m):
    return {k: Fraction(comb(m, k), 2 ** m) for k in range(m + 1)}


def same(a, b):
    keys = set(a) | set(b)
    return all(a.get(k, 0) == b.get(k, 0) for k in keys)


def rand_corr(rng, nA, nB, ties=False, zeros=False):
    vals = [Fraction(rng.randint(-9, 9), 10) for _ in range(nA * nB)]
    if not ties:
        vals = [Fraction(rng.randint(-10 ** 6, 10 ** 6), 10 ** 6) for _ in range(nA * nB)]
    if not zeros:
        vals = [v if v != 0 else Fraction(1, 10 ** 7) for v in vals]
    return [vals[i * nB:(i + 1) * nB] for i in range(nA)]


# ---------------------------------------------------------------- E1: S3.2 vs brute force
def e1():
    rng = random.Random(20261121)
    n_ok = n_cases = n_valid = 0
    n_tie_cases = 0
    for trial in range(400):
        nA = rng.randint(2, 7)
        nB = rng.randint(1, 6)
        ties = trial % 2 == 0
        C = rand_corr(rng, nA, nB, ties=ties, zeros=False)
        tau = Fraction(rng.choice([0, 0, 3, 5]), 10)
        m, npl, nz, match = site_stat(C, tau)
        if m == 0:
            continue
        n_cases += 1
        n_tie_cases += ties
        bl = brute_law_target(C, tau)
        cl = cluster_law(match)
        ok = cl is not None and same(bl, cl)
        n_ok += ok
        check("E1 cluster law == brute force", ok, f"trial {trial}")
        # validity of the p-value P(N+ >= obs) over the uniform orbit
        worst = Fraction(0)
        nB_ = len(C[0])
        pv = []
        for e in itertools.product((1, -1), repeat=nB_):
            _, o, _, _ = site_stat(flip_cols(C, e), tau)
            pv.append(sum(w for k, w in bl.items() if k >= o))
        for a in sorted(set(pv)):
            frac = Fraction(sum(1 for p in pv if p <= a), len(pv))
            worst = max(worst, frac - a)
        n_valid += worst <= 0
        check("E1 p-value super-uniform", worst <= 0, f"trial {trial} excess {worst}")
    return dict(cases=n_cases, with_ties=n_tie_cases, law_agree=n_ok, pvalue_valid=n_valid)


# ---------------------------------------------------------------- E1z: exact zero correlations
def e1_zero():
    """A kept pair with corr exactly 0 (tau = 0): c_i = 0 is neither + nor -."""
    C = [[Fraction(0), Fraction(0)], [Fraction(1, 2), Fraction(-1, 5)], [Fraction(-3, 10), Fraction(1, 10)]]
    m, npl, nz, match = site_stat(C, Fraction(0))
    bl = brute_law_target(C, Fraction(0))
    cl = cluster_law(match)
    binom = binom_law(m)
    return dict(m=m, nzero=nz, brute=str({k: str(v) for k, v in sorted(bl.items())}),
                formula=None if cl is None else str({k: str(v) for k, v in sorted(cl.items())}),
                formula_matches=(cl is not None and same(bl, cl)),
                binomial_m=str({k: str(v) for k, v in sorted(binom.items())}))


# ---------------------------------------------------------------- E2: S3.3 source-side binomial
def e2():
    rng = random.Random(7)
    agree = cases = clustered = 0
    for trial in range(300):
        nA = rng.randint(2, 8)
        nB = rng.randint(1, 4)          # few B units -> many clusters
        C = rand_corr(rng, nA, nB, ties=trial % 3 == 0, zeros=False)
        tau = Fraction(rng.choice([0, 2, 4]), 10)
        m, npl, nz, match = site_stat(C, tau)
        if m == 0:
            continue
        cases += 1
        js = [j for (_, j, _) in match]
        clustered += len(set(js)) < len(js)
        ok = same(brute_law_source(C, tau), binom_law(m))
        agree += ok
        check("E2 source-side flips give Binomial(m,1/2)", ok, f"trial {trial}")
    # same with zero correlations kept: expected to FAIL (control showing the zero-corr edge)
    Cz = [[Fraction(0), Fraction(0)], [Fraction(1, 2), Fraction(-1, 5)]]
    mz, _, nzz, _ = site_stat(Cz, Fraction(0))
    zero_breaks = not same(brute_law_source(Cz, Fraction(0)), binom_law(mz))
    return dict(cases=cases, with_clusters=clustered, binomial_exact=agree, zero_corr_breaks_binomial=zero_breaks)


# ---------------------------------------------------------------- E3: "Binomial exactly when every |s_j| = 1"
def e3():
    # one target unit matched by 3 source units with signs (+,+,-): |s| = 1 but not binomial
    match = [(0, 0, 1), (1, 0, 1), (2, 0, -1)]
    cl = cluster_law(match)
    b = binom_law(3)
    # also from a concrete corr matrix, by brute force
    C = [[Fraction(9, 10)], [Fraction(8, 10)], [Fraction(-7, 10)]]
    bl = brute_law_target(C, Fraction(0))
    return dict(match="3 sources -> 1 target, signs (+,+,-), |s|=1",
                law=str({k: str(v) for k, v in sorted(cl.items())}),
                brute=str({k: str(v) for k, v in sorted(bl.items())}),
                binomial3=str({k: str(v) for k, v in sorted(b.items())}),
                is_binomial=same(cl, b))


# ---------------------------------------------------------------- E4: same position (S4)
def elem_sym(ns, k):
    e = [1] + [0] * k
    for n in ns:
        for r in range(k, 0, -1):
            e[r] += e[r - 1] * n
    return e[k]


def rook_law(ns, N):
    R = len(ns)
    law = {}
    for k in range(R + 1):
        p = Fraction(0)
        for r in range(k, R + 1):
            p += (-1) ** (r - k) * comb(r, k) * elem_sym(ns, r) * Fraction(factorial(N - r), factorial(N))
        if p:
            law[k] = p
    return law


def matching_argmax(C):
    return [argmax_abs(row) for row in C]


def matching_bijective(C):
    nA, nB = len(C), len(C[0])
    best, bp = None, None
    for p in itertools.permutations(range(nB), nA):
        s = sum(abs(C[i][p[i]]) for i in range(nA))
        if best is None or s > best:
            best, bp = s, p
    return list(bp)


def e4():
    rng = random.Random(99)
    res = dict(argmax_cases=0, argmax_agree=0, bij_cases=0, bij_agree=0, bound_ok=0,
               tie_cases=0, tie_agree=0, tie_bound_ok=0)
    for trial in range(60):
        N = rng.randint(2, 6)
        hA = rng.randint(1, N)
        ties = trial % 4 == 3
        C = rand_corr(rng, hA, N, ties=ties, zeros=False)
        if ties:  # duplicate a B column to force exact ties
            for row in C:
                row[N - 1] = row[0]
        for kind in ("argmax", "bij"):
            if kind == "bij" and (ties or N > 5):
                continue
            mfun = matching_argmax if kind == "argmax" else matching_bijective
            law = {}
            for pi in itertools.permutations(range(N)):
                # B unit j gets label pi[j]: column pi[j] of the relabelled matrix is old column j
                Cp = [[None] * N for _ in range(hA)]
                for i in range(hA):
                    for j in range(N):
                        Cp[i][pi[j]] = C[i][j]
                mm = mfun(Cp)
                F = sum(1 for i in range(hA) if mm[i] == i)
                law[F] = law.get(F, 0) + Fraction(1, factorial(N))
            m0 = mfun(C)
            ns = {}
            for j in m0:
                ns[j] = ns.get(j, 0) + 1
            pred = rook_law(list(ns.values()), N)
            ok = same(law, pred)
            bound = all(sum(w for f, w in law.items() if f >= k) <= Fraction(1, factorial(k)) for k in range(1, hA + 1))
            if ties:
                res["tie_cases"] += 1
                res["tie_agree"] += ok
                res["tie_bound_ok"] += bound
                continue
            res[kind + "_cases"] += 1
            res[kind + "_agree"] += ok
            res["bound_ok"] += bound
            check(f"E4 {kind} rook law == brute force over relabellings", ok, f"trial {trial}")
            check("E4 1/k! bound", bound, f"trial {trial}")
    return res


# ---------------------------------------------------------------- E5: S3.5 numbers
def tail_low(m):  # P(N+/m < 0.335) = P(1000 N+ < 335 m)
    return Fraction(sum(comb(m, k) for k in range(m + 1) if 1000 * k < 335 * m), 2 ** m)


def tail_high(m):  # P(N+/m >= 0.585)
    return Fraction(sum(comb(m, k) for k in range(m + 1) if 1000 * k >= 585 * m), 2 ** m)


def e5():
    table = {m: (float(tail_low(m)), float(tail_high(m))) for m in (200, 256, 500, 1000)}
    worst_m, worst = None, Fraction(0)
    for m in range(200, 1001):
        t = tail_low(m)
        if t > worst:
            worst, worst_m = t, m
    union = {n: float(n * worst) for n in (100, 300, 496)}
    k200 = 200 * (Fraction(17, 50) / 3) ** 2
    k500 = 500 * (Fraction(17, 50) / 3) ** 2
    # 50 clusters of 4, all same sign: N+ = 100 + 2*sum e  ; share < 0.335 <=> N+ <= 66
    ex = Fraction(sum(comb(50, k) for k in range(51) if 1000 * (100 + 2 * (2 * k - 50)) < 335 * 200), 2 ** 50)
    return dict(table={m: f"{a:.4g} / {b:.4g}" for m, (a, b) in table.items()},
                max_low_tail=float(worst), at_m=worst_m, union=union,
                kappa200=str(k200), kappa500=str(k500), example_50x4=float(ex))


def main():
    out = {}
    out["E1_cluster_law"] = e1()
    out["E1z_zero_corr"] = e1_zero()
    out["E2_source_binomial"] = e2()
    out["E3_abs_s_one_counterexample"] = e3()
    out["E4_same_position"] = e4()
    out["E5_site_sentence"] = e5()
    for k, v in out.items():
        print(k, v)
    print("FAILURES", len(FAIL), FAIL[:5])
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
