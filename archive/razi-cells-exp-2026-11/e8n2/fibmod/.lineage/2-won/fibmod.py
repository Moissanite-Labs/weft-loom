import sys

MOD = 1_000_000_007
_SIZE0 = 65536
_SIZE1 = 30518

def _build_tables():
    T0_0 = [0] * _SIZE0
    T0_1 = [0] * _SIZE0
    a, b = 0, 1
    for i in range(_SIZE0):
        T0_0[i] = a
        T0_1[i] = b
        a, b = b, (a + b) % MOD

    s0, s1 = a, b
    sd = (s1 - s0) % MOD
    T1_0 = [0] * _SIZE1
    T1_d = [0] * _SIZE1
    x0, x1 = 0, 1
    for i in range(_SIZE1):
        T1_0[i] = x0
        T1_d[i] = (x1 - x0) % MOD
        x0, x1 = (x0 * sd + x1 * s0) % MOD, (x0 * s0 + x1 * s1) % MOD

    return tuple(T0_0), tuple(T0_1), tuple(T1_0), tuple(T1_d)

_T0_0, _T0_1, _T1_0, _T1_d = _build_tables()

def fib(
    n: int,
    T0_0=_T0_0,
    T0_1=_T0_1,
    T1_0=_T1_0,
    T1_d=_T1_d,
) -> int:
    if n <= 0:
        return 0
    n %= 2000000016
    i0 = n & 65535
    i1 = n >> 16
    return (T0_0[i0] * T1_d[i1] + T0_1[i0] * T1_0[i1]) % 1000000007

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(fib(int(sys.argv[1])))
