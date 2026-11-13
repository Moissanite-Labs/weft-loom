import sys
M = 1000000007
# p = 1e9+7 is 2 mod 5, so the Pisano period divides 2(p+1) = 2000000016 < 2**31.

def _fib_once(n):
    # One-shot path (command line): fast doubling, no table to build.
    n %= 2000000016
    a, b = 0, 1
    for ch in bin(n)[2:]:
        c = a * (2 * b - a) % M
        d = (a * a + b * b) % M
        if ch == '1':
            a, b = d, (c + d) % M
        else:
            a, b = c, d
    return a

if __name__ == '__main__':
    print(_fib_once(int(sys.argv[1])))
else:
    # Imported for repeated calls: split the reduced n into 10+10+11 bits and combine
    # precomputed (F(k), F(k+1)) pairs with F(a+b) = F(a)F(b+1) + F(a-1)F(b).
    def _table(step, count):
        s, s1 = step
        out = [(0, 1)]
        a, a1 = 0, 1
        for _ in range(count - 1):
            a, a1 = (a * s1 + (a1 - a) * s) % M, (a1 * s1 + a * s) % M
            out.append((a, a1))
        return out, ((a * s1 + (a1 - a) * s) % M, (a1 * s1 + a * s) % M)
    _T0, _s = _table((1, 1), 2048)      # F(i), i < 2^11
    _T1, _s = _table(_s, 1024)          # F(j * 2^11)
    _T2, _s = _table(_s, 954)           # F(k * 2^21), k*2^21 < 2000000016

    def fib(n, T0=_T0, T1=_T1, T2=_T2, M=M):
        n %= 2000000016
        a, a1 = T2[n >> 21]
        b, b1 = T1[(n >> 11) & 1023]
        c = (a * b1 + (a1 - a) * b) % M
        c1 = (a1 * b1 + a * b) % M
        d, d1 = T0[n & 2047]
        return (c * d1 + (c1 - c) * d) % M
