import sys
from math import isqrt

def count_primes(n: int) -> int:
    if n <= 2:
        return 0
    m = n - 1
    if m < 100000:
        size = n // 2
        sieve = bytearray(b'\x01') * size
        sieve[0] = 0
        for i in range(3, isqrt(n) + 1, 2):
            if sieve[i >> 1]:
                start = (i * i) >> 1
                sieve[start::i] = b'\x00' * ((size - 1 - start) // i + 1)
        return sieve.count(1) + 1

    r = isqrt(m)
    small = [(i + 1) >> 1 for i in range(r + 1)]
    large = [0] + [((m // i) + 1) >> 1 for i in range(1, r + 1)]

    for p in range(3, r + 1, 2):
        if small[p] > small[p - 1]:
            sp = small[p - 1]
            p2 = p * p
            mp = m // p
            max_i = min(r, mp // p)
            limit1 = min(r // p, max_i)
            for i in range(1, limit1 + 1, 2):
                large[i] -= large[i * p] - sp
            for i in range((limit1 + 1) | 1, max_i + 1, 2):
                large[i] -= small[mp // i] - sp
            for q in range(r // p, p - 1, -1):
                d = small[q] - sp
                qp = q * p
                end = r + 1 if qp + p > r else qp + p
                for v in range(qp, end):
                    small[v] -= d

    return large[1]

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
