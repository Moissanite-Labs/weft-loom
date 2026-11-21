"""Exact power of the paired sign test used by the ratchet.

Model: n episodes, each in one of three states for the pair (first, second):
the first passes and the second does not (probability p), the reverse
(probability q), or no difference (the rest). The test is the ratchet's: the
first wins if it has more discordant passes and the exact one-sided sign test is
at most alpha, and the comparison counts only with at least MIN_DISCORDANT
discordant episodes (the preregistration's rule).

Power is the exact probability of that outcome, as a fraction, from the
multinomial law with integer arithmetic. p and q are given as integers over
`den`.

    python3 power.py [N]          prints the table used in PREREG.md

The power of the whole rule needs both training seeds on set 1 and then the
confirmation on set 2. It is approximated here as power ** 3 for equal effects,
which assumes the three tests are independent. They are not exactly: the same
adapter is tested on both sets, so the true joint power is somewhat higher. The
stratum and format conditions of the rule can only lower it, and are not
modelled. The figure is a guide, not a guarantee.
"""
import os
import sys
from fractions import Fraction
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ratchet  # noqa: E402

MIN_DISCORDANT = 10
ALPHA = ratchet.DEFAULT_ALPHA


class PowerError(Exception):
    pass


def min_wins(d, alpha=ALPHA):
    """Fewest first-only episodes that reject among d discordant ones (the first
    must also have more wins than losses), or None. Same rule as
    ratchet.sign_test_p, summed from the top."""
    if d < MIN_DISCORDANT:
        return None
    tail, best = 0, None
    for a in range(d, d // 2, -1):
        tail += comb(d, a)
        if tail * alpha.denominator > alpha.numerator * 2 ** d:
            break
        best = a
    return best


def power(n, p_num, q_num, den, alpha=ALPHA):
    """Exact probability, as a Fraction, that the first beats the second."""
    r_num = den - p_num - q_num
    if min(p_num, q_num, r_num) < 0 or den < 1 or n < 1:
        raise PowerError("p, q and the rest must be non-negative parts of den")
    pp, qp, rp = [[1] for _ in range(3)]
    for _ in range(n):
        pp.append(pp[-1] * p_num)
        qp.append(qp[-1] * q_num)
        rp.append(rp[-1] * r_num)
    total = 0
    for d in range(MIN_DISCORDANT, n + 1):
        a_min = min_wins(d, alpha)
        if a_min is None:
            continue
        c = comb(d, a_min)
        inner = 0
        for a in range(a_min, d + 1):
            inner += c * pp[a] * qp[d - a]
            c = c * (d - a) // (a + 1)
        total += comb(n, d) * rp[n - d] * inner
    return Fraction(total, den ** n)


def rule_power(single):
    """Approximate power of the whole rule: both seeds and the confirmation."""
    return single ** 3


def table(n, discordant_shares=(15, 25, 35), effects=(2, 3, 4, 5, 6, 8)):
    """Rows of (discordant share, net effect, power of one test), shares and
    effects in percent. p = (d + e) / 2 and q = (d - e) / 2 percent, so p is
    (d + e) / 200 and q is (d - e) / 200."""
    rows = []
    for d in discordant_shares:
        for e in effects:
            if e <= d:
                rows.append((d, e, power(n, d + e, d - e, 200)))
    return rows


TARGET = Fraction(4, 5)


def rule_power_at(n, share, halves):
    """Whole-rule power (the cube) when the discordant share is `share` percent
    and the net effect is `halves` half points: p = (share + e) / 200 and
    q = (share - e) / 200, which over 400 is (2 share + halves) and (2 share - halves)."""
    return rule_power(power(n, 2 * share + halves, 2 * share - halves, 400))


def min_effect_halves(n, share, target=TARGET):
    """The smallest net effect, in half percentage points, whose whole-rule
    power (the cube of the single power) is at least target; None if even an
    effect equal to the discordant share does not reach it. Found by bisection:
    power does not fall as the effect grows."""
    lo, hi = 1, 2 * share
    if rule_power_at(n, share, hi) < target:
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if rule_power_at(n, share, mid) >= target:
            hi = mid
        else:
            lo = mid + 1
    return lo


def halves_text(h):
    return "%d.%d" % (h // 2, 5 * (h % 2))


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 1000
    print("n = %d paired episodes, alpha = %s, at least %d discordant" % (n, ALPHA, MIN_DISCORDANT))
    print("%-12s %-12s %-14s %-14s" % ("discordant", "net effect", "power, one test", "whole rule (approx)"))
    for d, e, w in table(n):
        print("%-12s %-12s %-14s %-14s" % ("%d%%" % d, "%d points" % e, "%.4f" % (w.numerator / w.denominator),
                                           "%.4f" % (rule_power(w).numerator / rule_power(w).denominator)))
    print()
    print("Smallest net effect (points) with whole-rule power of at least %s (cube of the single power):" % TARGET)
    for d in (15, 25, 35):
        h = min_effect_halves(n, d)
        print("%-12s %s" % ("%d%%" % d, "none up to the discordant share" if h is None else halves_text(h)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
