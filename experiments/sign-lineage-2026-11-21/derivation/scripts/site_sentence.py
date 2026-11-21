"""Exact test of the site's sentence (task text): unrelated pairs with at least
200 strong matches land between 33 and 59 percent sign agreement.

Question: is that spread, over a few hundred pairs, compatible with each pair's
count being Binomial(m, 1/2)? Integers and Fractions only. No bare assert.
Run: python3 -I -B site_sentence.py  (also -I -O -B and -I -B -W error)
"""
import json
import sys
from fractions import Fraction
from math import comb


class CheckFailure(Exception):
    pass


def require(cond, msg):
    if not cond:
        raise CheckFailure(msg)


def lower_tail(m, k):
    if k < 0:
        return Fraction(0)
    return Fraction(sum(comb(m, x) for x in range(0, min(k, m) + 1)), 2 ** m)


def upper_tail(m, k):
    if k > m:
        return Fraction(0)
    return Fraction(sum(comb(m, x) for x in range(max(k, 0), m + 1)), 2 ** m)


def sci(q, digits=4):
    """Exact Fraction -> decimal string 'd.ddde-N' by integer arithmetic (truncated)."""
    if q == 0:
        return "0"
    require(q > 0, "sci expects a positive value")
    num, den = q.numerator, q.denominator
    e = len(str(num)) - len(str(den))
    # adjust e until 10^e <= q < 10^(e+1)
    while True:
        lo = Fraction(10) ** e
        if lo <= q < lo * 10:
            break
        e += 1 if q >= lo * 10 else -1
    mant = q / Fraction(10) ** e
    scaled = (mant.numerator * 10 ** (digits - 1)) // mant.denominator
    s = str(scaled)
    return "%s.%se%d" % (s[0], s[1:], e)


def main():
    out = {}
    # Rounding conservatively: a reported "33%" means npos/m < 0.335, "59%" means npos/m >= 0.585.
    lo_cut, hi_cut = Fraction(335, 1000), Fraction(585, 1000)
    rows = []
    worst_lo = worst_hi = None
    for m in range(200, 1001):
        k_lo = -(-lo_cut.numerator * m // lo_cut.denominator) - 1  # largest k with k/m < 0.335
        k_hi = -(-hi_cut.numerator * m // hi_cut.denominator)      # smallest k with k/m >= 0.585
        require(Fraction(k_lo, m) < lo_cut <= Fraction(k_lo + 1, m), "k_lo cut")
        require(Fraction(k_hi - 1, m) < hi_cut <= Fraction(k_hi, m), "k_hi cut")
        pl, ph = lower_tail(m, k_lo), upper_tail(m, k_hi)
        worst_lo = pl if worst_lo is None or pl > worst_lo else worst_lo
        worst_hi = ph if worst_hi is None or ph > worst_hi else worst_hi
        if m in (200, 256, 300, 400, 500, 1000):
            rows.append({"m": m, "k_low_max": k_lo, "P_share_le_33pct": sci(pl),
                         "k_high_min": k_hi, "P_share_ge_59pct": sci(ph)})
    out["per_pair_binomial_tails"] = rows
    out["max_over_m_200_to_1000_P_low"] = sci(worst_lo)
    out["max_over_m_200_to_1000_P_high"] = sci(worst_hi)
    # Union bound over K pairs (valid with any dependence between pairs that share a model)
    ub = []
    for K in (100, 300, 496):
        ub.append({"pairs_K": K, "union_bound_any_pair_le_33pct": sci(K * worst_lo),
                   "union_bound_any_pair_ge_59pct": sci(K * worst_hi)})
    out["union_bound_over_pairs"] = ub
    # Cluster form: sd(share) = sqrt(sum s_j^2)/(2m) = sqrt(kappa/m)/2 with kappa = sum s_j^2 / m.
    # For a share q to sit z standard deviations out, kappa = m (2|q-1/2|)^2 / z^2.
    kap = []
    for q in (Fraction(33, 100), Fraction(59, 100)):
        for z in (3, 4):
            for m in (200, 500):
                kap.append({"share": str(q), "z": z, "m": m,
                            "kappa_needed": str(Fraction(m) * (2 * abs(q - Fraction(1, 2))) ** 2 / (z * z)),
                            "kappa_needed_approx": sci(Fraction(m) * (2 * abs(q - Fraction(1, 2))) ** 2 / (z * z), 3)})
    out["cluster_kappa_needed"] = kap
    # Exact cluster example: m=200 matches in 50 same-sign clusters of 4 (kappa=4)
    J, v, m = 50, 4, 200
    counts = {}
    for x in range(J + 1):
        S = v * (2 * x - J)
        counts[S] = counts.get(S, 0) + comb(J, x)
    den = 2 ** J
    p_lo = Fraction(sum(c for S, c in counts.items() if (m + S) // 2 < Fraction(335, 1000) * m), den)
    out["cluster_example_m200_50x4_P_share_lt_33.5pct"] = sci(p_lo)
    out["cluster_example_union_bound_496_pairs"] = sci(496 * p_lo)
    print(json.dumps(out, sort_keys=True, indent=1))


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as e:
        print("CHECK FAILED:", e)
        sys.exit(1)
