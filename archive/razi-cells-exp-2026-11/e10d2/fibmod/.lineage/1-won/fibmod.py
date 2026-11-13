import sys
M = 1_000_000_007
P = 2 * (M + 1)  # Pisano period of M divides 2(M+1) since M is prime, M % 5 == 2
SH = 15
S = 1 << SH

def _build():
    # L[k] = (F(k), F(k+1)) for k < S
    L = [None] * S
    a, b = 0, 1
    for k in range(S):
        L[k] = (a, b)
        a, b = b, (a + b) % M
    fS, fS1 = a, b            # F(S), F(S+1)
    fSm1 = (fS1 - fS) % M     # F(S-1)
    nh = (P >> SH) + 2
    H = [None] * nh
    a, b = 0, 1               # F(m), F(m+1) with m = k*S
    for k in range(nh):
        H[k] = (a, b)
        a, b = (b * fS + a * fSm1) % M, (b * fS1 + a * fS) % M
    return L, H

_L, _H = _build()

def fib(n, _L=_L, _H=_H, _M=M, _P=P, _mask=S - 1):
    n %= _P
    fm, fm1 = _H[n >> 15]
    fk, fk1 = _L[n & _mask]
    # F(m+k) = F(m+1)F(k) + F(m)F(k-1), F(k-1) = F(k+1) - F(k)
    return (fm1 * fk + fm * (fk1 - fk)) % _M

if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
