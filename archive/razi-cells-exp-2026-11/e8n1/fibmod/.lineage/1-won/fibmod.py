import sys

MOD = 1_000_000_007
PISANO = 2_000_000_016

def _build_tables():
    mod = MOD
    t0_0 = [0] * 1024
    t0_1 = [0] * 1024
    a, b = 0, 1
    for i in range(1024):
        t0_0[i] = a
        t0_1[i] = b
        a, b = b, (a + b) % mod

    s1_0, s1_1 = a, b
    s1_diff = (s1_1 - s1_0) % mod
    t1_0 = [0] * 1024
    t1_1 = [0] * 1024
    a, b = 0, 1
    for i in range(1024):
        t1_0[i] = a
        t1_1[i] = b
        a, b = (a * s1_diff + b * s1_0) % mod, (a * s1_0 + b * s1_1) % mod

    s2_0, s2_1 = a, b
    s2_diff = (s2_1 - s2_0) % mod
    t2_0 = [0] * 2048
    t2_1 = [0] * 2048
    a, b = 0, 1
    for i in range(2048):
        t2_0[i] = a
        t2_1[i] = b
        a, b = (a * s2_diff + b * s2_0) % mod, (a * s2_0 + b * s2_1) % mod

    # Precompute (d - c) % mod for t1 and t2 to save a subtraction per call
    t1_d = [(t1_1[i] - t1_0[i]) % mod for i in range(1024)]
    t2_d = [(t2_1[i] - t2_0[i]) % mod for i in range(2048)]
    return t0_0, t0_1, t1_0, t1_1, t1_d, t2_0, t2_d

_T0_0, _T0_1, _T1_0, _T1_1, _T1_D, _T2_0, _T2_D = _build_tables()

def fib_mod(n: int, mod: int = 1_000_000_007,
            _t0_0=_T0_0, _t0_1=_T0_1,
            _t1_0=_T1_0, _t1_1=_T1_1, _t1_d=_T1_D,
            _t2_0=_T2_0, _t2_d=_T2_D) -> int:
    if n <= 0:
        return 0
    if mod != 1_000_000_007:
        a, b = 0, 1
        for bit in bin(n)[2:]:
            c = (a * ((b << 1) - a)) % mod
            d = (a * a + b * b) % mod
            if bit == '1':
                a, b = d, (c + d) % mod
            else:
                a, b = c, d
        return a

    rem = n % 2_000_000_016
    c0 = rem & 1023
    c1 = (rem >> 10) & 1023
    c2 = rem >> 20

    a = _t0_0[c0]
    b = _t0_1[c0]

    if c1:
        c = _t1_0[c1]
        na = (a * _t1_d[c1] + b * c) % 1_000_000_007
        b = (a * c + b * _t1_1[c1]) % 1_000_000_007
        a = na

    if c2:
        a = (a * _t2_d[c2] + b * _t2_0[c2]) % 1_000_000_007

    return a

if __name__ == '__main__':
    print(fib_mod(int(sys.argv[1])))
