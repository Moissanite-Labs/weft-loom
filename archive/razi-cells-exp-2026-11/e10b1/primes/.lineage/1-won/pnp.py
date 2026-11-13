import sys


def count_primes(n):
    if n < 6:
        return (0, 0, 0, 1, 2, 2)[n] if n > 0 else 0
    if n < 2000000:
        size = n // 3 + (n % 6 == 2)
        sieve = bytearray([1]) * size
        for i in range(1, int(n ** 0.5) // 3 + 1):
            if sieve[i]:
                k = (3 * i + 1) | 1
                s = k * k // 3
                st = 2 * k
                sieve[s::st] = bytes(len(range(s, size, st)))
                s = k * (k - 2 * (i & 1) + 4) // 3
                sieve[s::st] = bytes(len(range(s, size, st)))
        return sieve.count(1) + 1
    import numpy as np
    size = n // 3 + (n % 6 == 2)
    sieve = np.ones(size, dtype=np.bool_)
    for i in range(1, int(n ** 0.5) // 3 + 1):
        if sieve[i]:
            k = (3 * i + 1) | 1
            sieve[k * k // 3::2 * k] = False
            sieve[k * (k - 2 * (i & 1) + 4) // 3::2 * k] = False
    return int(np.count_nonzero(sieve)) + 1


if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
