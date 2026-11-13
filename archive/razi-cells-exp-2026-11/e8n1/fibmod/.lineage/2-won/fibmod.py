import sys

MOD = 1_000_000_007
PISANO = 2_000_000_016

def _build_tables():
    mod = 1_000_000_007
    t0_0 = [0] * 32768
    t0_1 = [0] * 32768
    a, b = 0, 1
    for i in range(32768):
        t0_0[i] = a
        t0_1[i] = b
        a, b = b, (a + b) % mod

    s0, s1 = a, b
    s_diff = (s1 - s0) % mod
    t1_0 = [0] * 65536
    t1_d = [0] * 65536
    a, b = 0, 1
    for i in range(65536):
        t1_0[i] = a
        t1_d[i] = (b - a) % mod
        a, b = (a * s_diff + b * s0) % mod, (a * s0 + b * s1) % mod

    return tuple(t0_0), tuple(t0_1), tuple(t1_0), tuple(t1_d)

_T0_0, _T0_1, _T1_0, _T1_D = _build_tables()

def fib_mod(n: int,
            _t0_0=_T0_0, _t0_1=_T0_1,
            _t1_0=_T1_0, _t1_d=_T1_D) -> int:
    if n <= 0:
        return 0
    rem = n % 2_000_000_016
    c0 = rem & 32767
    c1 = rem >> 15
    return (_t0_0[c0] * _t1_d[c1] + _t0_1[c0] * _t1_0[c1]) % 1_000_000_007

if __name__ == '__main__':
    print(fib_mod(int(sys.argv[1])))
