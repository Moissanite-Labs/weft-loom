import sys
import numpy as np

SEG = 4194304

def count_primes(n):
    if n < 3:
        return 0
    half = (n + 1) // 2
    lim = int(n ** 0.5)
    while (lim + 1) * (lim + 1) <= n:
        lim += 1
    bh = (lim + 1) // 2
    b = np.ones(bh, dtype=bool)
    b[0] = False
    i = 1
    while (2 * i + 1) * (2 * i + 1) <= lim:
        if b[i]:
            p = 2 * i + 1
            b[(p * p) // 2::p] = False
        i += 1
    primes = (2 * np.nonzero(b)[0] + 1).tolist()
    if SEG <= 0:
        seg = np.ones(half, dtype=bool)
        seg[0] = False
        for p in primes:
            seg[p * p // 2::p] = False
        return 1 + int(np.count_nonzero(seg))
    total = 1
    for lo in range(0, half, SEG):
        hi = lo + SEG
        if hi > half:
            hi = half
        seg = np.ones(hi - lo, dtype=bool)
        if lo == 0:
            seg[0] = False
        for p in primes:
            if p * p // 2 >= hi:
                break
            start = p * p // 2
            if start < lo:
                v = 2 * lo + 1
                k = (v + p - 1) // p
                if k % 2 == 0:
                    k += 1
                start = (k * p) // 2
            if start < hi:
                seg[start - lo::p] = False
        total += int(np.count_nonzero(seg))
    return total

print(count_primes(int(sys.argv[1])))
