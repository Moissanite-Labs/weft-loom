import os
import sys
import ctypes
from math import isqrt

_c_count_primes = None
try:
    _so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libprimes.so")
    if os.path.exists(_so_path):
        _lib = ctypes.CDLL(_so_path)
        _c_count_primes = _lib.count_primes
        _c_count_primes.argtypes = [ctypes.c_int64]
        _c_count_primes.restype = ctypes.c_int64
except Exception:
    _c_count_primes = None

def _pi(N: int) -> int:
    if N < 2:
        return 0
    if N == 2:
        return 1
    if N == 3:
        return 2
    if N == 4:
        return 2
    if N == 5:
        return 3

    v = isqrt(N)
    smalls = [(i - 1) >> 1 for i in range(v + 1)]
    s = (v + 1) >> 1
    roughs = [2 * i + 1 for i in range(s)]
    larges = [(N // (2 * i + 1) - 1) >> 1 for i in range(s)]
    skip = bytearray(v + 1)

    p_cnt = 0
    for p in range(3, v + 1, 2):
        if not skip[p]:
            q = p * p
            if q * q > N:
                break
            skip[p] = 1
            for i in range(q, v + 1, 2 * p):
                skip[i] = 1
            ns = 0
            for k in range(s):
                i = roughs[k]
                if skip[i]:
                    continue
                d = i * p
                larges[ns] = (
                    larges[k]
                    - (larges[smalls[d] - p_cnt] if d <= v else smalls[N // d])
                    + p_cnt
                )
                roughs[ns] = i
                ns += 1
            s = ns
            i = v
            for j in range((v // p - 1) | 1, p - 1, -2):
                c = smalls[j] - p_cnt
                e = j * p
                while i >= e:
                    smalls[i] -= c
                    i -= 1
            p_cnt += 1

    ans0 = larges[0] + (s + 2 * (p_cnt - 1)) * (s - 1) // 2 - sum(larges[1:s])
    for l in range(1, s):
        q = roughs[l]
        M = N // q
        e = smalls[M // q] - p_cnt
        if e <= l:
            break
        t = 0
        for k in range(l + 1, e + 1):
            t += smalls[M // roughs[k]]
        ans0 += t - (e - l) * (p_cnt + l - 1)

    return ans0 + 1

def _py_count_primes(n: int) -> int:
    if n <= 2:
        return 0
    return _pi(n - 1)

if _c_count_primes is not None:
    count_primes = _c_count_primes
else:
    count_primes = _py_count_primes

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
