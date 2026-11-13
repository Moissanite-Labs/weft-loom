import sys
from math import isqrt


def count_primes(n):
    """Count primes strictly below n."""
    if n < 3:
        return 0
    size = n >> 1                      # odd numbers 1,3,5,... < n ; index i -> 2i+1
    sieve = bytearray(b'\x01') * size
    sieve[0] = 0                       # 1 is not prime
    limit = isqrt(n - 1)
    for i in range(1, (limit >> 1) + 1):
        if sieve[i]:
            p = 2 * i + 1
            start = 2 * i * (i + 1)    # index of p*p
            sieve[start::p] = bytes((size - 1 - start) // p + 1)
    return sieve.count(1) + 1          # +1 for 2


def main():
    print(count_primes(int(sys.argv[1])))


if __name__ == '__main__':
    main()
