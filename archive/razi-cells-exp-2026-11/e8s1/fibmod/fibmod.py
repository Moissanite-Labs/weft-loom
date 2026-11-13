import sys

MOD = 1_000_000_007

def _build():
    t0_a = [0] * 65536
    t0_b = [1] * 65536
    ca, cb = 0, 1
    for i in range(1, 65536):
        ca, cb = cb, (ca + cb) % MOD
        t0_a[i] = ca
        t0_b[i] = cb
    a, b = cb, (ca + cb) % MOD

    t1_c = [0] * 30518
    t1_dmc = [1] * 30518
    ca, cb = 0, 1
    amba = (b - a) % MOD
    for i in range(1, 30518):
        ca, cb = (ca * amba + cb * a) % MOD, (ca * a + cb * b) % MOD
        t1_c[i] = ca
        t1_dmc[i] = (cb - ca) % MOD
    return tuple(t0_a), tuple(t0_b), tuple(t1_c), tuple(t1_dmc)

T0A, T0B, T1C, T1DMC = _build()

def solve(n, _T0A=T0A, _T0B=T0B, _T1C=T1C, _T1DMC=T1DMC):
    n %= 2_000_000_016
    lo = n & 65535
    hi = n >> 16
    return (_T0A[lo] * _T1DMC[hi] + _T0B[lo] * _T1C[hi]) % 1_000_000_007

fib = solve

if __name__ == "__main__":
    print(solve(int(sys.argv[1])))
