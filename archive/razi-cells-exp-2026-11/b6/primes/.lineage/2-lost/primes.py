import sys
from math import isqrt


def count_primes(n):
    if n <= 3:
        return int(n > 2)
    size = n // 3 + (n % 6 == 2)
    sieve = bytearray(b'\x01') * size
    sieve[0] = 0
    for i in range(1, isqrt(n - 1) // 3 + 1):
        if sieve[i]:
            p = (3 * i + 1) | 1
            start = p * p // 3
            step = 2 * p
            sieve[start::step] = b'\0' * ((size - start - 1) // step + 1)
            start = p * (p - 2 * (i & 1) + 4) // 3
            sieve[start::step] = b'\0' * ((size - start - 1) // step + 1)
    return 2 + sieve.count(1)


if __name__ == '__main__':
    print(count_primes(int(sys.argv[1])))
