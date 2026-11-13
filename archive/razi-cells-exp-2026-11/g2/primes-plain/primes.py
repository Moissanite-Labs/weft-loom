import sys
from math import isqrt


def prime_count(n: int) -> int:
    if n < 3:
        return 0
    size = n // 2
    sieve = bytearray(size)
    limit = isqrt(n - 1)
    for i in range(1, (limit + 1) // 2):
        if not sieve[i]:
            p = 2 * i + 1
            start = (p * p) // 2
            if start < size:
                sieve[start::p] = b'\x01' * ((size - start - 1) // p + 1)
    return sieve.count(0)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: primes.py N")
    print(prime_count(int(sys.argv[1])))


if __name__ == "__main__":
    main()
