import sys
from math import isqrt

R = (1, 7, 11, 13, 17, 19, 23, 29)


def _small(n):
    if n < 6:
        return (0, 0, 0, 1, 2, 2)[n] if n > 0 else 0
    size = n // 3 + (n % 6 == 2)
    sieve = bytearray([1]) * size
    for i in range(1, isqrt(n) // 3 + 1):
        if sieve[i]:
            k = (3 * i + 1) | 1
            st = 2 * k
            s = k * k // 3
            sieve[s::st] = bytes(len(range(s, size, st)))
            s = k * (k - 2 * (i & 1) + 4) // 3
            sieve[s::st] = bytes(len(range(s, size, st)))
    return sieve.count(1) + 1


def count_primes(n):
    """mod-30 wheel, 8 residue arrays."""
    if n < 1000:
        return _small(n)
    arrs = {r: bytearray(b'\x01') * ((n - r + 29) // 30) for r in R}
    arrs[1][0] = 0
    table = []
    for r in R:
        row = []
        for q in R:
            t = r * q % 30
            row.append((q if q >= r else q + 30, arrs[t], len(arrs[t])))
        table.append((r, arrs[r], row))
    for a in range(isqrt(n) // 30 + 1):
        b = 30 * a
        for r, ar, row in table:
            if ar[a]:
                p = b + r
                for q, at, lt in row:
                    s = p * (b + q) // 30
                    at[s::p] = bytes(len(range(s, lt, p)))
    return sum(arrs[r].count(1) for r in R) + 3


if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
