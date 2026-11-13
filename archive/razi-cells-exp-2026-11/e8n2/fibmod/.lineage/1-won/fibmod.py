import sys

MOD = 1_000_000_007
_SIZE = 32768

def _build_tables():
    T0_0 = [0] * _SIZE
    T0_1 = [0] * _SIZE
    a, b = 0, 1
    for i in range(_SIZE):
        T0_0[i] = a
        T0_1[i] = b
        a, b = b, (a + b) % MOD

    def next_table(prev_0, prev_1):
        # step is F(2^15*k) for k = _SIZE, i.e. combine(prev[_SIZE-1], prev[1])
        a0, a1 = prev_0[_SIZE - 1], prev_1[_SIZE - 1]
        b0, b1 = prev_0[1], prev_1[1]
        s0 = (a0 * (b1 - b0) + a1 * b0) % MOD
        s1 = (a0 * b0 + a1 * b1) % MOD
        sd = s1 - s0

        cur_0 = [0] * _SIZE
        cur_1 = [0] * _SIZE
        cur_d = [0] * _SIZE
        x0, x1 = 0, 1
        for i in range(_SIZE):
            cur_0[i] = x0
            cur_1[i] = x1
            cur_d[i] = x1 - x0
            x0, x1 = (x0 * sd + x1 * s0) % MOD, (x0 * s0 + x1 * s1) % MOD
        return cur_0, cur_1, cur_d

    T1_0, T1_1, T1_d = next_table(T0_0, T0_1)
    T2_0, T2_1, _ = next_table(T1_0, T1_1)
    T3_0, T3_1, T3_d = next_table(T2_0, T2_1)
    return T0_0, T0_1, T1_0, T1_1, T1_d, T2_0, T2_1, T3_0, T3_1, T3_d

_T0_0, _T0_1, _T1_0, _T1_1, _T1_d, _T2_0, _T2_1, _T3_0, _T3_1, _T3_d = _build_tables()

def fib(
    n: int,
    T0_0=_T0_0,
    T0_1=_T0_1,
    T1_0=_T1_0,
    T1_1=_T1_1,
    T1_d=_T1_d,
    T2_0=_T2_0,
    T2_1=_T2_1,
    T3_0=_T3_0,
    T3_1=_T3_1,
    T3_d=_T3_d,
) -> int:
    if n <= 0:
        return 0
    i0 = n & 32767
    i1 = (n >> 15) & 32767
    i2 = (n >> 30) & 32767
    i3 = n >> 45
    a0 = T0_0[i0]
    a1 = T0_1[i0]
    b0 = T1_0[i1]
    p0 = a0 * T1_d[i1] + a1 * b0
    p1 = a0 * b0 + a1 * T1_1[i1]
    c0 = T2_0[i2]
    c1 = T2_1[i2]
    d0 = T3_0[i3]
    q0 = c0 * T3_d[i3] + c1 * d0
    q1 = c0 * d0 + c1 * T3_1[i3]
    return (p0 * (q1 - q0) + p1 * q0) % 1000000007

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(fib(int(sys.argv[1])))
