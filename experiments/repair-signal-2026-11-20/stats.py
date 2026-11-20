"""Exact paired tests, standard library only."""
from fractions import Fraction
from math import comb


def sign_test(wins, losses, alternative="greater"):
    """Exact binomial test on discordant pairs. wins = pairs where the first
    arm did better. 'greater' tests first arm better. 'two-sided' doubles the
    smaller tail, capped at 1."""
    n = wins + losses
    if n == 0:
        return 1.0
    def upper(k):  # P(X >= k)
        return Fraction(sum(comb(n, i) for i in range(k, n + 1)), 2 ** n)
    if alternative == "greater":
        return float(upper(wins))
    if alternative == "two-sided":
        return float(min(Fraction(1), 2 * min(upper(wins), upper(losses))))
    raise ValueError(alternative)


def signflip_test(diffs):
    """Exact one-sided paired sign-flip test on integer differences.
    Statistic is the sum of differences. P(sum under random signs >= observed)."""
    d = [abs(int(x)) for x in diffs if int(x) != 0]
    obs = sum(int(x) for x in diffs)
    dist = {0: 1}
    for a in d:
        new = {}
        for s, c in dist.items():
            new[s + a] = new.get(s + a, 0) + c
            new[s - a] = new.get(s - a, 0) + c
        dist = new
    total = 2 ** len(d)
    return float(Fraction(sum(c for s, c in dist.items() if s >= obs), total))
