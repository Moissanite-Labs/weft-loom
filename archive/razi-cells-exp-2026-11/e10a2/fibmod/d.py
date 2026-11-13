import sys
M = 1000000007
_T = []
_a, _b = 0, 1
for _i in range(1025):
    _T.append(_a)
    _a, _b = _b, (_a + _b) % M
def fib(n):
    q, n = divmod(n, 1000000008)
    neg = q & 1
    if n > 500000004:
        neg ^= n & 1
        n = 1000000008 - n
    if n < 1024:
        r = _T[n]
        return -r % M if neg else r
    k = n >> (n.bit_length() - 10)
    a = _T[k]
    b = _T[k + 1]
    s = bin(n)
    for c in s[12:-1]:
        d = a * (2 * b - a) % M
        e = (a * a + b * b) % M
        if c == '1':
            a, b = e, (d + e) % M
        else:
            a, b = d, e
    if s[-1] == '1':
        r = (a * a + b * b) % M
    else:
        r = a * (2 * b - a) % M
    return -r % M if neg else r
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
