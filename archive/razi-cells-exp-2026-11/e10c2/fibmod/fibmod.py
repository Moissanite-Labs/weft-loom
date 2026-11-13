import sys
M = 1_000_000_007
P = 2 * (M + 1)
SH = 16
S = 1 << SH
MASK = S - 1
lo = [0] * (S + 2)
a, b = 0, 1
for i in range(S + 2):
    lo[i] = a
    a, b = b, (a + b) % M
FS, FS1 = lo[S], lo[S + 1]
H = P // S + 2
hiF = [0] * H
hiFm1 = [0] * H
a, b = 0, 1
for h in range(H):
    hiF[h] = a
    hiFm1[h] = (b - a) % M
    a, b = (a * FS1 + (b - a) * FS) % M, (b * FS1 + a * FS) % M

def fib(n, _lo=lo, _hf=hiF, _hm=hiFm1, _P=P, _M=M, _SH=SH, _MASK=MASK):
    n %= _P
    h = n >> _SH
    k = n & _MASK
    return (_hf[h] * _lo[k + 1] + _hm[h] * _lo[k]) % _M

if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
