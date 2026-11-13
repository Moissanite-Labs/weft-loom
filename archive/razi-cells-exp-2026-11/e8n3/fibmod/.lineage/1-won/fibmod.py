import sys

MOD = 1_000_000_007
PISANO = 2_000_000_016

def _fast_fib(n: int) -> int:
    n %= PISANO
    if n == 0:
        return 0
    a, b = 0, 1
    for bit in range(n.bit_length() - 1, -1, -1):
        c = (a * ((b << 1) - a)) % MOD
        d = (a * a + b * b) % MOD
        if (n >> bit) & 1:
            a, b = d, (c + d) % MOD
        else:
            a, b = c, d
    return a

if __name__ == '__main__':
    print(_fast_fib(int(sys.argv[1])))
else:
    def _build():
        T0 = [0] * 65536
        T1 = [0] * 65536
        a, b = 1, 0
        for i in range(65536):
            T0[i] = a
            T1[i] = b
            a, b = b, (a + b) % MOD
        s0, s1 = a, b
        s01 = (s0 + s1) % MOD

        M = 30518
        U0 = [0] * M
        U1 = [0] * M
        A, B = 0, 1
        for j in range(M):
            U0[j] = A
            U1[j] = B
            A, B = (A * s0 + B * s1) % MOD, (A * s1 + B * s01) % MOD

        def fib(n: int, _T0=T0, _T1=T1, _U0=U0, _U1=U1, _P=PISANO, _M=MOD) -> int:
            n %= _P
            lo = n & 65535
            hi = n >> 16
            return (_U0[hi] * _T0[lo] + _U1[hi] * _T1[lo]) % _M

        return fib

    fib = _build()
