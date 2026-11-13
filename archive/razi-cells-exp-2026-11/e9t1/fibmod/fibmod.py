import sys

def _build():
    t0 = [None] * 32768
    a, b = 0, 1
    for i in range(32768):
        t0[i] = (a, b)
        a, b = b, (a + b) % 1000000007
    sa, sb = a, b
    sdmc = (sb - sa) % 1000000007

    t1 = [None] * 61036
    ca, cb = 0, 1
    for i in range(61036):
        t1[i] = ((cb - ca) % 1000000007, ca)
        ca, cb = (ca * sdmc + cb * sa) % 1000000007, (ca * sa + cb * sb) % 1000000007
    return t0, t1

_T0, _T1 = _build()

def fibmod(n: int, _T0=_T0, _T1=_T1) -> int:
    n %= 2000000016
    a, b = _T0[n & 0x7FFF]
    c, d = _T1[n >> 15]
    return (a * c + b * d) % 1000000007

if __name__ == "__main__":
    print(fibmod(int(sys.argv[1])))
