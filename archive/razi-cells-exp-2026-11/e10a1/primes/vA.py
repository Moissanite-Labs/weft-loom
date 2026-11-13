import sys
from math import isqrt


def count_primes(n):
    if n < 3:
        return 0
    m = n // 2
    if m < 64:
        sieve = bytearray(b'\x01') * m
        sieve[0] = 0
        i = 1
        while 2 * i * (i + 1) < m:
            if sieve[i]:
                s = 2 * i * (i + 1)
                sieve[s::2 * i + 1] = bytes(len(range(s, m, 2 * i + 1)))
            i += 1
        return sieve.count(1) + 1
    tp = (3, 5, 7, 11, 13, 17) if m > 1000000 else (3, 5, 7, 11, 13)
    P = 1
    for p in tp:
        P *= p
    pat = bytearray(b'\x01') * P
    for p in tp:
        pat[p // 2::p] = bytes(len(range(p // 2, P, p)))
    sieve = pat * (m // P + 1)
    del sieve[m:]
    sieve[0] = 0
    for p in tp:
        sieve[p // 2] = 1
    for i in range(tp[-1] // 2 + 1, (isqrt(n - 1) + 1) // 2):
        if sieve[i]:
            s = 2 * i * (i + 1)
            p = 2 * i + 1
            sieve[s::p] = bytes((m - s - 1) // p + 1)
    return sieve.count(1) + 1


if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
