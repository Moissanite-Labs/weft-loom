import sys
from math import isqrt

SMALL = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
         67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137,
         139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199)


def count_primes(n):
    if n < 200:
        c = 0
        for p in SMALL:
            if p < n:
                c += 1
        return c
    # wheel mod 6: index i <-> number (3*i+1)|1 : 1,5,7,11,13,...
    M = n // 3
    while ((3 * M + 1) | 1) < n:
        M += 1
    while ((3 * (M - 1) + 1) | 1) >= n:
        M -= 1
    tp = (5, 7, 11, 13, 17) if M > 400000 else (5, 7, 11, 13)
    L = 2
    for p in tp:
        L *= p
    pat = bytearray(b'\x01') * L
    for p in tp:
        st = 2 * p
        s = p // 3
        pat[s::st] = bytes(len(range(s, L, st)))
        s = 5 * p // 3
        pat[s::st] = bytes(len(range(s, L, st)))
    sieve = pat * (M // L + 1)
    del sieve[M:]
    sieve[0] = 0
    for p in tp:
        sieve[p // 3] = 1
    for i in range(tp[-1] // 3 + 1, isqrt(n - 1) // 3 + 1):
        if sieve[i]:
            k = (3 * i + 1) | 1
            st = 2 * k
            s = k * k // 3
            sieve[s::st] = bytes(len(range(s, M, st)))
            s = k * (k + 4 - 2 * (i & 1)) // 3
            sieve[s::st] = bytes(len(range(s, M, st)))
    return sieve.count(1) + 2


if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
