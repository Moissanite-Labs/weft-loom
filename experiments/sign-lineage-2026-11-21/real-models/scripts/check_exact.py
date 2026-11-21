"""Test exactlaw.py against brute-force enumeration on small cases. Brute force here shares no code with exactlaw.

Run: python3 -I -B check_exact.py   (also -I -O -B and -I -B -W error). Exit 1 on any mismatch.
Includes controls that must fail (a perturbed law must be caught).
"""
import itertools
import os
import random
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exactlaw as X  # noqa: E402

FAIL = []


def check(cond, msg):
    if not cond:
        FAIL.append(msg)


def brute_binom(m):
    law = [0] * (m + 1)
    for bits in itertools.product((0, 1), repeat=m):
        law[sum(bits)] += 1
    return [Fraction(c, 2 ** m) for c in law]


def brute_cluster(clusters):
    """clusters: list of lists of source signs (+1/-1) matched to one target unit each. Enumerate target flips."""
    J = len(clusters)
    m = sum(len(c) for c in clusters)
    law = {}
    for e in itertools.product((1, -1), repeat=J):
        npos = 0
        for ej, cl in zip(e, clusters):
            for c in cl:
                if ej * c > 0:
                    npos += 1
        law[npos] = law.get(npos, 0) + 1
    return {k: Fraction(v, 2 ** J) for k, v in law.items()}, m


def brute_same_position(layers_match):
    """layers_match: list of (N, hA, match) with match[a] = target index in the same layer for source unit a, or None
    if source unit a is matched elsewhere. Enumerate all relabellings (product of permutations)."""
    perms = [list(itertools.permutations(range(N))) for N, _, _ in layers_match]
    law = {}
    tot = 0
    for combo in itertools.product(*perms):
        F = 0
        for (N, hA, match), p in zip(layers_match, combo):
            for a in range(hA):
                j = match[a]
                if j is not None and p[j] == a:
                    F += 1
        law[F] = law.get(F, 0) + 1
        tot += 1
    return {k: Fraction(v, tot) for k, v in law.items()}


def main():
    rng = random.Random(20261121)
    n_cases = 0
    # 1. binomial tails, all k, m <= 12
    for m in range(0, 13):
        law = brute_binom(m)
        for k in range(-1, m + 2):
            ge = sum((law[i] for i in range(len(law)) if i >= k), Fraction(0))
            le = sum((law[i] for i in range(len(law)) if i <= k), Fraction(0))
            check(X.binom_tail_ge(m, k) == ge, "binom ge m=%d k=%d" % (m, k))
            check(X.binom_tail_le(m, k) == le, "binom le m=%d k=%d" % (m, k))
            n_cases += 1
    # 2. cluster law vs brute force, random clusterings
    n_cl = 0
    for trial in range(300):
        J = rng.randint(1, 9)
        clusters = []
        for _ in range(J):
            size = rng.choice([1, 1, 1, 2, 3, 4, 5])
            clusters.append([rng.choice((1, -1)) for _ in range(size)])
        law, m = brute_cluster(clusters)
        svals = [sum(c) for c in clusters]
        for k in range(0, m + 1):
            ge = sum((p for kk, p in law.items() if kk >= k), Fraction(0))
            le = sum((p for kk, p in law.items() if kk <= k), Fraction(0))
            r = X.cluster_test(svals, m, k)
            check(r["exact"] and r["p_upper"] == ge and r["p_lower"] == le, "cluster trial %d k %d" % (trial, k))
            n_cl += 1
    # control that must fail: shift one cluster's sign sum by 2 (keeps parity)
    clusters = [[1, 1, 1], [1, -1, 1], [1], [-1, -1]]
    law, m = brute_cluster(clusters)
    bad = [sum(c) for c in clusters]
    bad[0] -= 2
    control_cluster_caught = any(
        X.cluster_test(bad, m, k)["p_upper"] != sum((p for kk, p in law.items() if kk >= k), Fraction(0))
        for k in range(m + 1))
    check(control_cluster_caught, "cluster control not caught")
    # one-to-one clusters give the binomial exactly
    for m in (1, 5, 17, 40):
        for k in range(m + 1):
            r = X.cluster_test([rng.choice((1, -1)) for _ in range(m)], m, k)
            check(r["p_upper"] == X.binom_tail_ge(m, k), "cluster one-to-one m=%d k=%d" % (m, k))
    # the refuter's counterexample: three sources with (+,+,-) onto one target: law {1:1/2, 2:1/2}
    r1 = X.cluster_test([1], 3, 2)
    check(r1["p_upper"] == Fraction(1, 2) and X.cluster_test([1], 3, 1)["p_upper"] == 1, "refuter 3-to-1 case")
    # cap path returns a bound flagged inexact
    rcap = X.cluster_test([1] * 10 + [2] * 5 + [3] * 4, 10 + 10 + 12, 20, cap=1)
    check(rcap["exact"] is False and 0 < rcap["hoeffding_upper"] <= 1, "cap path")
    # 3. same-position law vs enumeration of all relabellings
    n_sp = 0
    for trial in range(120):
        L = rng.randint(1, 2)
        layers_match = []
        layers_ns = []
        for _ in range(L):
            N = rng.randint(1, 5)
            hA = rng.randint(1, N)
            match = []
            for a in range(hA):
                match.append(rng.randrange(N) if rng.random() < 0.8 else None)
            counts = {}
            for j in match:
                if j is not None:
                    counts[j] = counts.get(j, 0) + 1
            layers_match.append((N, hA, match))
            layers_ns.append((N, list(counts.values())))
        if sum(len(range(N)) for N, _, _ in layers_match) > 9:
            continue
        law = brute_same_position(layers_match)
        mylaw = X.same_position_law_exact(layers_ns)
        for k in range(0, 12):
            want = law.get(k, Fraction(0))
            got = mylaw[k] if k < len(mylaw) else Fraction(0)
            check(want == got, "same-pos law trial %d k %d" % (trial, k))
            ge = sum((p for kk, p in law.items() if kk >= k), Fraction(0))
            r = X.same_position_test(layers_ns, k)
            if r.get("exact"):
                check(r["p_upper"] == ge, "same-pos test exact trial %d k %d" % (trial, k))
            else:
                lo, hi = r["bracket"]
                check(lo <= ge <= hi, "same-pos bracket trial %d k %d" % (trial, k))
            # truncated bracket must contain truth
            r2 = X.same_position_test(layers_ns, k, extra=1)
            if not r2.get("exact") and "bracket" in r2:
                lo, hi = r2["bracket"]
                check(lo <= ge <= hi, "same-pos short bracket trial %d k %d" % (trial, k))
            n_sp += 1
        mean = sum((kk * p for kk, p in law.items()), Fraction(0))
        check(X.same_position_test(layers_ns, 1)["mean"] == mean, "same-pos mean trial %d" % trial)
    # Cantelli lower bound below the mean: three layers of a full one-to-one matching (mean 3), k = 1, 2
    lm = [(4, 4, [0, 1, 2, 3]), (3, 3, [2, 0, 1]), (3, 2, [0, 0])]
    law = brute_same_position(lm)
    lns = [(4, [1, 1, 1, 1]), (3, [1, 1, 1]), (3, [2])]
    n_cant = 0
    for k in (1, 2):
        ge = sum((p for kk, p in law.items() if kk >= k), Fraction(0))
        r = X.same_position_test(lns, k, extra=0)
        if "bracket" in r:
            check(r["bracket"][0] <= ge <= r["bracket"][1], "cantelli bracket k %d" % k)
            n_cant += r.get("lower_from") == "cantelli"
    print("cantelli cases", n_cant)
    # bracket on a larger case (no enumeration): must be ordered and within [0, 1]
    big = [(64, [1] * 30 + [2] * 10)] * 4
    rb = X.same_position_test(big, 6, extra=6)
    okb = ("bracket" in rb and 0 <= rb["bracket"][0] <= rb["bracket"][1] <= 1) or rb.get("exact")
    check(okb, "big bracket ordering")
    rbound = X.same_position_test(big, 400)
    check(rbound["exact"] is False and rbound["bound_upper"] == Fraction(4 ** 400, __import__("math").factorial(400)),
          "kmax bound")
    # control that must fail: a wrong layer width
    law = brute_same_position([(3, 3, [0, 0, 2])])
    wrong = X.same_position_law_exact([(4, [2, 1])])
    control_sp_caught = wrong[0] != law.get(0, Fraction(0))
    check(control_sp_caught, "same-pos control not caught")
    print("binomial cases", n_cases)
    print("cluster cases", n_cl)
    print("same-position cases", n_sp)
    print("control cluster caught", control_cluster_caught)
    print("control same-position caught", control_sp_caught)
    print("failures", len(FAIL))
    for f in FAIL[:20]:
        print("FAIL", f)
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    main()
