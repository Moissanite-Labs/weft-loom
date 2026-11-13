import sys
M = 1000000007
P = 2000000016
K = 32768
_L = [0, 1]
for _i in range(K + 2):
    _L.append((_L[-1] + _L[-2]) % M)
_fK, _fK1, _fK2 = _L[K], _L[K + 1], _L[K + 2]
_HA = []
_HB = []
_a, _b = 0, 1
for _h in range((P >> 15) + 2):
    _HA.append(_a)
    _c = _b - _a
    _HB.append(_c % M)
    _a, _b = (_a * _fK1 + _c * _fK) % M, (_a * _fK2 + _c * _fK1) % M
_L1 = _L[1:]
def fib(n, _L=_L, _L1=_L1, _HA=_HA, _HB=_HB, P=P, M=M):
    n %= P
    h = n >> 15
    n &= 32767
    return (_HA[h] * _L1[n] + _HB[h] * _L[n]) % M
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
