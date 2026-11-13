import sys
from math import isqrt

SMALL = (3, 5, 7, 11, 13)
PERIOD = 3 * 5 * 7 * 11 * 13
SEGLEN = 1 << 20

def small_primes(limit):
    # odd primes <= limit, > 13
    if limit < 3:
        return []
    size = limit // 2 + 1
    sv = bytearray([1]) * size
    sv[0] = 0
    r = isqrt(limit)
    for i in range(1, r // 2 + 1):
        if sv[i]:
            p = 2 * i + 1
            st = p * p // 2
            sv[st::p] = bytes(len(range(st, size, p)))
    return [2 * i + 1 for i in range(7, size) if sv[i]]

def count_primes(n):
    if n < 3:
        return 0
    size = n // 2  # index i -> number 2i+1
    r = isqrt(n - 1)
    primes = small_primes(r)
    template = bytearray([1]) * (SEGLEN + PERIOD)
    for p in SMALL:
        st = (p - 1) // 2
        template[st::p] = bytes(len(range(st, len(template), p)))
    zeros = bytes(SEGLEN // 17 + 2)
    count = 0
    lo = 0
    while lo < size:
        hi = lo + SEGLEN
        if hi > size:
            hi = size
        L = hi - lo
        off = lo % PERIOD
        seg = template[off:off + L]
        lo2 = 2 * lo + 1
        for p in primes:
            s = p * p // 2
            if s >= hi:
                break
            if s < lo:
                m = -(-lo2 // p) * p
                if not m & 1:
                    m += p
                s = m // 2
            s -= lo
            cnt = (L - s + p - 1) // p
            if cnt > 0:
                seg[s::p] = zeros[:cnt]
        if lo == 0:
            seg[0] = 0
            for p in SMALL:
                k = (p - 1) // 2
                if k < L:
                    seg[k] = 1
        count += seg.count(1)
        lo = hi
    return 1 + count

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
