import sys
from math import isqrt


def count_primes(n):
    """Count primes p < n using a mod-6 wheel bytearray sieve."""
    if n < 6:
        return (0, 0, 0, 1, 2, 2)[n] if n > 0 else 0
    size = n // 3 + (n % 6 == 2)
    sieve = bytearray([1]) * size
    for i in range(1, isqrt(n) // 3 + 1):
        if sieve[i]:
            k = (3 * i + 1) | 1
            s = k * k // 3
            st = 2 * k
            sieve[s::st] = bytes(len(range(s, size, st)))
            s = k * (k - 2 * (i & 1) + 4) // 3
            sieve[s::st] = bytes(len(range(s, size, st)))
    return sieve.count(1) + 1  # +2 for primes 2,3; -1 for index 0 (the number 1)


if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
