import sys
from math import isqrt

def count_primes(n: int) -> int:
    m = n - 1
    if m < 2:
        return 0
    if m == 2:
        return 1
    r = isqrt(m)
    small = [(i + 1) >> 1 for i in range(r + 1)]
    large = [0] * (r + 1)
    for i in range(1, r + 1, 2):
        large[i] = (m // i + 1) >> 1

    for p in range(3, r + 1, 2):
        pc = small[p - 1]
        if small[p] > pc:
            p2 = p * p
            max_i = m // p2
            if max_i > r:
                max_i = r
            mid_i = r // p
            if mid_i > max_i:
                mid_i = max_i
            for i in range(1, mid_i + 1, 2):
                large[i] -= large[i * p] - pc
            for i in range((mid_i | 1) if (mid_i & 1 == 0) else mid_i + 2, max_i + 1, 2):
                large[i] -= small[m // (i * p)] - pc
            for v in range(r, p2 - 1, -1):
                small[v] -= small[v // p] - pc
    return large[1]

if __name__ == '__main__':
    print(count_primes(int(sys.argv[1])))
