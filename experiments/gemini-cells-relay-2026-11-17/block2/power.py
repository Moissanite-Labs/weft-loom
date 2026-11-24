#!/usr/bin/env python3
"""Power of the exact two-sided permutation test that block 2 plans to use, by simulation.

Two arms of n runs each. Each run's value is the mean builder-assay gain of its final
harnesses. Values are drawn from normal distributions whose means differ by d, with the
same standard deviation sd in both arms. The test is the plan's: the difference of arm
means, two-sided, exact over every relabelling, at alpha 0.05. Standard library only.

    python3 -I -B power.py > power.out

The pilot's own numbers, for scale (record README, builder assay): over every fault-free
run, mean gains were +0.020 (one score, free lineages, 4 runs) and +0.492 (solo, 4 runs),
a difference of 0.47. Per-run spread inside an arm was up to about 0.3 (solo: +0.275 to
+0.556). A pilot's largest difference is likely to shrink when measured again, so the table
also gives a half and a quarter of it.
"""

import itertools
import random

ALPHA = 0.05
SIMS = 2000
SEED = 20261124


def exact_p(a, b):
    """Two-sided exact permutation p for the difference of means."""
    pooled = a + b
    n, total = len(a), sum(a) + sum(b)
    observed = abs(sum(a) / n - sum(b) / len(b))
    hits = count = 0
    for idx in itertools.combinations(range(len(pooled)), n):
        s = sum(pooled[i] for i in idx)
        diff = abs(s / n - (total - s) / len(b))
        hits += diff >= observed - 1e-12
        count += 1
    return hits / count


def power(n, d, sd, rng, sims):
    rejections = 0
    for _ in range(sims):
        a = [rng.gauss(0.0, sd) for _ in range(n)]
        b = [rng.gauss(d, sd) for _ in range(n)]
        rejections += exact_p(a, b) <= ALPHA
    return rejections / sims


def main():
    rng = random.Random(SEED)
    print(f"Exact two-sided permutation test, alpha {ALPHA}, {SIMS} simulations per cell"
          f" ({SIMS // 4} for n = 8), seed {SEED}.\n")
    print("Smallest attainable p: " + ", ".join(
        f"n={n}: {2 / len(list(itertools.combinations(range(2 * n), n))):.4f}" for n in (3, 4, 5, 6, 8)))
    print()
    print(f"{'n per arm':>9} {'sd':>5} " + " ".join(f"{'d=' + format(d, '.3f'):>9}" for d in (0.12, 0.24, 0.47)))
    for n in (3, 4, 5, 6, 8):
        for sd in (0.10, 0.20, 0.30):
            sims = SIMS // 4 if n == 8 else SIMS
            cells = [power(n, d, sd, rng, sims) for d in (0.12, 0.24, 0.47)]
            print(f"{n:9d} {sd:5.2f} " + " ".join(f"{c:9.2f}" for c in cells))


if __name__ == "__main__":
    main()
