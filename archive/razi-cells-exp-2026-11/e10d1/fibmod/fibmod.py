import sys
M = 1_000_000_007
# Pisano period of M (M = 2 mod 5 => period divides 2(M+1)); verified in bench.
P = 2 * (M + 1)
# n < P < 2^31: split n = hi*2^16 + lo; F(a+b) = F(a)F(b+1) + F(a-1)F(b)
_SH = 16
_LMASK = (1 << _SH) - 1

def _table(count, step):
    # returns lists F(k*step), F(k*step+1) for k in range(count)
    fa, fb = [0] * count, [0] * count
    # compute F(step), F(step+1) by doubling
    def _fd(n):
        a, b = 0, 1
        for bit in bin(n)[2:]:
            c = a * ((b << 1) - a) % M
            d = (a * a + b * b) % M
            if bit == '1':
                a, b = d, (c + d) % M
            else:
                a, b = c, d
        return a, b
    s0, s1 = _fd(step)
    sm1 = (s1 - s0) % M
    a, b = 0, 1
    for k in range(count):
        fa[k] = a
        fb[k] = b
        # (a,b) = F(k*step), F(k*step+1) -> advance by step
        a, b = (a * s1 + (b - a) * s0) % M, (a * s0 + b * s1) % M
    return fa, fb

_LO, _LO1 = _table(1 << _SH, 1)
_HI, _HI1 = _table((P >> _SH) + 1, 1 << _SH)
_HIm1 = [(y - x) % M for x, y in zip(_HI, _HI1)]

def fib(n):
    n %= P
    hi = n >> _SH
    lo = n & _LMASK
    return (_HI[hi] * _LO1[lo] + _HIm1[hi] * _LO[lo]) % M

if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
