import sys

MOD = 1_000_000_007

def _build():
    mod = 1_000_000_007
    a0 = [0] * 65536
    a1 = [0] * 65536
    a, b = 0, 1
    for i in range(65536):
        a0[i] = a
        a1[i] = b
        a, b = b, (a + b) % mod

    s_prev, s_curr, s_next = (b - a) % mod, a, b
    b0 = [0] * 30518
    b1 = [0] * 30518
    pm1, p0, p1 = 1, 0, 1
    for j in range(30518):
        b0[j] = pm1
        b1[j] = p0
        np0 = (p0 * s_prev + p1 * s_curr) % mod
        np1 = (p0 * s_curr + p1 * s_next) % mod
        pm1, p0, p1 = (np1 - np0) % mod, np0, np1

    return a0, a1, b0, b1

_A0, _A1, _B0, _B1 = _build()

def fib(n, _a0=_A0, _a1=_A1, _b0=_B0, _b1=_B1):
    n %= 2_000_000_016
    lo = n & 65535
    hi = n >> 16
    return (_a0[lo] * _b0[hi] + _a1[lo] * _b1[hi]) % 1_000_000_007

if __name__ == '__main__':
    n = int(sys.argv[1])
    print(fib(n))
