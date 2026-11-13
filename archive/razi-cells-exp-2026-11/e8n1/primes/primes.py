import sys
import os
import ctypes

def _load_c_lib():
    so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_primes.so")
    if os.path.exists(so_path):
        try:
            lib = ctypes.CDLL(so_path)
            fn = lib.count_primes_below
            fn.argtypes = [ctypes.c_int64]
            fn.restype = ctypes.c_int64
            return fn
        except Exception:
            return None
    return None

_c_count_primes = _load_c_lib()
_acc6 = None

def _get_acc6():
    global _acc6
    if _acc6 is None:
        from itertools import accumulate
        phi6 = bytearray([1]) * 30030
        for p in (2, 3, 5, 7, 11, 13):
            phi6[0::p] = bytearray(30030 // p)
        _acc6 = list(accumulate(phi6, initial=0))
    return _acc6

def sieve_count(n: int) -> int:
    import math
    if n <= 2:
        return 0
    if n == 3:
        return 1
    size = n // 2
    sieve = bytearray([1]) * size
    sieve[0] = 0
    limit = math.isqrt(n - 1) // 2
    for i in range(1, limit + 1):
        if sieve[i]:
            p = 2 * i + 1
            start = (p * p) // 2
            sieve[start::p] = bytearray((size - start - 1) // p + 1)
    return sieve.count(1) + 1

def sieve_primes(limit: int):
    import math
    if limit < 2:
        return []
    size = (limit + 1) // 2
    sieve = bytearray([1]) * size
    sieve[0] = 0
    r = math.isqrt(limit) // 2
    for i in range(1, r + 1):
        if sieve[i]:
            p = 2 * i + 1
            start = (p * p) // 2
            sieve[start::p] = bytearray((size - start - 1) // p + 1)
    primes = [2]
    primes.extend(2 * i + 1 for i, v in enumerate(sieve) if v)
    return primes

def count_primes(n: int) -> int:
    if n <= 2:
        return 0
    if _c_count_primes is not None:
        return int(_c_count_primes(n))
    if n <= 300_000:
        return sieve_count(n)

    import math
    from bisect import bisect_right

    x = n - 1
    y = int(x ** 0.38)
    z = x // y

    primes = sieve_primes(z)

    def pi(v: int) -> int:
        return bisect_right(primes, v)

    a = pi(y)
    b = pi(math.isqrt(x))

    p2 = 0
    for i in range(a, b):
        p2 += pi(x // primes[i]) - i

    acc6 = _get_acc6()
    memo = {}

    def phi(v: int, c: int) -> int:
        if c == 0:
            return v
        if c == 1:
            return (v + 1) >> 1
        if c == 2:
            return v - (v >> 1) - v // 3 + v // 6
        if c == 6:
            q, r = divmod(v, 30030)
            return q * 5760 + acc6[r + 1]
        if v < primes[c - 1]:
            return 1 if v > 0 else 0
        key = (v << 12) | c
        res = memo.get(key)
        if res is not None:
            return res
        res = phi(v, c - 1) - phi(v // primes[c - 1], c - 1)
        memo[key] = res
        return res

    return phi(x, a) + a - 1 - p2

if __name__ == "__main__":
    n = int(sys.argv[1])
    print(count_primes(n))
