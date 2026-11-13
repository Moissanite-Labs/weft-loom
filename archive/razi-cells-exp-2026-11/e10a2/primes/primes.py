import sys, os
from math import isqrt

W = 8
SEG = 1 << 20


def simple(n):
    if n < 3:
        return 0
    h = n // 2
    s = bytearray([1]) * h
    s[0] = 0
    i = 1
    while True:
        p = 2 * i + 1
        if p * p >= n:
            break
        if s[i]:
            st = (p * p) // 2
            s[st::p] = bytes(len(range(st, h, p)))
        i += 1
    return s.count(1) + 1


def work(lo0, hi0, primes, sq, pat, period):
    nxt = []
    for p in primes:
        st = p * p // 2
        if st >= hi0:
            break
        if st < lo0:
            st = lo0 + ((p // 2 - lo0) % p)
        nxt.append(st)
    np_ = len(nxt)
    total = 0
    for lo in range(lo0, hi0, SEG):
        hi = lo + SEG
        if hi > hi0:
            hi = hi0
        off = lo % period
        buf = pat[off:off + hi - lo]
        for j in range(np_):
            st = nxt[j]
            if st < hi:
                p = primes[j]
                k = (hi - st + p - 1) // p
                buf[st - lo::p] = bytes(k)
                nxt[j] = st + k * p
            elif sq[j] >= hi:
                break
        total += buf.count(1)
    return total


def count(n):
    if n < 65536:
        return simple(n)
    h = n // 2
    period = 15015
    base = bytearray([1]) * period
    for p in (3, 5, 7, 11, 13):
        base[p // 2::p] = bytes(len(range(p // 2, period, p)))
    pat = base * (SEG // period + 2)
    r = isqrt(n - 1)
    m = r // 2 + 1
    b = bytearray([1]) * m
    i = 1
    while True:
        p = 2 * i + 1
        if p * p > r:
            break
        if b[i]:
            st = (p * p) // 2
            b[st::p] = bytes(len(range(st, m, p)))
        i += 1
    primes = [2 * i + 1 for i in range(8, m) if b[i]]
    sq = [p * p // 2 for p in primes]
    w = W if h >= (1 << 21) else 1
    if w == 1:
        return work(0, h, primes, sq, pat, period) + 5
    chunk = -(-h // w)
    fds = []
    for k in range(1, w):
        lo0 = k * chunk
        hi0 = min(h, lo0 + chunk)
        if lo0 >= hi0:
            break
        rfd, wfd = os.pipe()
        if os.fork() == 0:
            try:
                os.write(wfd, str(work(lo0, hi0, primes, sq, pat, period)).encode())
            finally:
                os._exit(0)
        os.close(wfd)
        fds.append(rfd)
    total = work(0, min(h, chunk), primes, sq, pat, period) + 5
    for rfd in fds:
        total += int(os.read(rfd, 64))
    return total


if __name__ == "__main__":
    print(count(int(sys.argv[1])))
