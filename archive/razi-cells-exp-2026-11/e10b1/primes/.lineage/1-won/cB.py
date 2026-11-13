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
    """mod-6 wheel with presieve of 5..17 by pattern replication."""
    if n < 1000:
        return _small(n)
    size = n // 3 + (n % 6 == 2)
    pat = bytearray([1]) * 170170
    for k in (5, 7, 11, 13, 17):
        z = bytes(85085 // k)
        pat[k // 3::2 * k] = z
        pat[5 * k // 3::2 * k] = z
    sieve = pat * (size // 170170 + 1)
    del sieve[size:]
    sieve[1:6] = b'\x01\x01\x01\x01\x01'
    for i in range(6, isqrt(n) // 3 + 1):
        if sieve[i]:
            k = (3 * i + 1) | 1
            st = 2 * k
            s = k * k // 3
            sieve[s::st] = bytes(len(range(s, size, st)))
            s = k * (k - 2 * (i & 1) + 4) // 3
            sieve[s::st] = bytes(len(range(s, size, st)))
    return sieve.count(1) + 1


if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
