"""Second checker for power.py. Shares no code with it: uses scipy.stats
binomial laws in floating point instead of exact integer sums, and a separate
search for the rejection threshold. Needs scipy (the system python3 has it).

    python3 -I -B checks/power_crosscheck.py

Compares the single-test power at n = 1000 with the figures printed by
power.py (copied below, four decimals) and exits 1 if any differs by more
than 0.00006.
"""
import sys

from scipy.stats import binom

N = 1000
ALPHA = 1 / 40
MIN_DISCORDANT = 10

# (discordant percent, net effect points, power of one test as printed by power.py 1000)
PRINTED = [
    (15, 2, 0.3423), (15, 3, 0.6625), (15, 4, 0.8953), (15, 5, 0.9824), (15, 6, 0.9985), (15, 8, 1.0000),
    (25, 2, 0.2245), (25, 3, 0.4513), (25, 4, 0.6968), (25, 5, 0.8763), (25, 6, 0.9643), (25, 8, 0.9991),
    (35, 2, 0.1726), (35, 3, 0.3415), (35, 4, 0.5510), (35, 5, 0.7475), (35, 6, 0.8864), (35, 8, 0.9892),
]


def threshold(d):
    """Smallest win count that rejects among d discordant, by scanning upward."""
    if d < MIN_DISCORDANT:
        return None
    for a in range(d // 2 + 1, d + 1):
        if binom.sf(a - 1, d, 0.5) <= ALPHA:
            return a
    return None


def power(share, effect):
    p = (share + effect) / 200.0
    q = (share - effect) / 200.0
    total = 0.0
    for d in range(MIN_DISCORDANT, N + 1):
        a = threshold(d)
        if a is None:
            continue
        total += binom.pmf(d, N, p + q) * binom.sf(a - 1, d, p / (p + q))
    return total


def main():
    worst = 0.0
    for share, effect, printed in PRINTED:
        mine = power(share, effect)
        worst = max(worst, abs(mine - printed))
        print("%d%% %d points: scipy %.5f printed %.4f" % (share, effect, mine, printed))
    print("largest difference %.6f" % worst)
    return 0 if worst <= 0.00006 else 1


if __name__ == "__main__":
    sys.exit(main())
