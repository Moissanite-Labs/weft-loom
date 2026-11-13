import sys
from math import isqrt


def count_primes(n: int) -> int:
    if n <= 2:
        return 0
    # Odd-only sieve: index i represents odd number 2*i + 1.
    size = n // 2
    sieve = bytearray(b'\x01') * size
    sieve[0] = 0  # 1 is not prime
    limit = isqrt(n - 1)
    for p in range(3, limit + 1, 2):
        if sieve[p >> 1]:
            start = (p * p) >> 1
            step = p
            sieve[start::step] = b'\x00' * (((size - 1 - start) // step) + 1)
    # Add the only even prime, 2.
    return sieve.count(1) + 1


if __name__ == '__main__':
    sys.stdout.write(str(count_primes(int(sys.argv[1]))) + '\n')
