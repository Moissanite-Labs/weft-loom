import sys

M = 1_000_000_007
# p = 5k+2  =>  Pisano period divides 2(p+1); also F(n+(p+1)) == -F(n) mod p.
H = M + 1          # < 2**30


def fib_dbl(n, M=M, H=H):
    """Fast doubling, no tables: cheapest for a single call (CLI)."""
    q, n = divmod(n, H)
    a, b = 0, 1
    for ch in bin(n)[2:]:
        c = a * (2 * b - a) % M
        d = (a * a + b * b) % M
        if ch == '1':
            a = d
            b = (c + d) % M
        else:
            a = c
            b = d
    return (M - a) % M if q & 1 else a


def _pair(n):
    a, b = 0, 1
    for ch in bin(n)[2:]:
        c = a * (2 * b - a) % M
        d = (a * a + b * b) % M
        if ch == '1':
            a, b = d, (c + d) % M
        else:
            a, b = c, d
    return a, b


def _table(step):
    # [(F(i*step), F(i*step+1)) for i in range(1024)]
    pa, pb = _pair(step)
    a, b = 0, 1
    T = []
    for _ in range(1024):
        T.append((a, b))
        a, b = (a * pb + (b - a) * pa) % M, (b * pb + a * pa) % M
    return T


_T0, _T1, _T2 = [], [], []


def _init():
    if not _T0:
        _T2.extend(_table(1 << 20))
        _T1.extend(_table(1 << 10))
        _T0.extend(_table(1))


def fib(n, M=M, H=H, T0=_T0, T1=_T1, T2=_T2):
    """Table version: reduce n mod (M+1), split into three 10-bit digits,
    combine with F(m+n) = F(m)F(n+1) + F(m-1)F(n). Tables built on first call."""
    q, n = divmod(n, H)
    try:
        a, b = T2[n >> 20]
    except IndexError:
        _init()
        a, b = T2[n >> 20]
    c, d = T1[(n >> 10) & 1023]
    e = (a * d + (b - a) * c) % M
    f = b * d + a * c
    c, d = T0[n & 1023]
    a = (e * d + (f - e) * c) % M
    return (M - a) % M if q & 1 else a


if __name__ == '__main__':
    print(fib_dbl(int(sys.argv[1])))
