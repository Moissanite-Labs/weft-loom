import sys
from math import isqrt


def prime_count(n):
    """Count primes strictly below n (odd-only sieve)."""
    if n < 3:
        return 0
    size = n >> 1
    s = bytearray(size)
    s[0] = 1  # 1 is not prime
    r = isqrt(n - 1)
    for i in range(1, (r - 1) // 2 + 1):
        if not s[i]:
            p = 2 * i + 1
            st = p * p >> 1
            s[st::p] = b'\x01' * ((size - st - 1) // p + 1)
    return 1 + size - s.count(1)


if __name__ == "__main__":
    sys.stdout.write(str(prime_count(int(sys.argv[1]))) + "\n")
