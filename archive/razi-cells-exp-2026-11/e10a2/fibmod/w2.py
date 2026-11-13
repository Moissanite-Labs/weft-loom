import sys
_W = []
_a, _b = 2, 3
for _i in range(1026):
    _W.append(_a)
    _a, _b = _b, (3 * _b - _a) % 1000000007
def fib(n):
    # W[m] = L(2m): W(2m) = W(m)^2 - 2, W(2m+1) = W(m)W(m+1) - 3
    # 5F(2m) = 2W(m+1) - 3W(m), 5F(2m+1) = W(m) + W(m+1)
    # p = 1e9+7: F(n+p+1) = -F(n), F(p+1-j) = (-1)^j F(j)
    q, n = divmod(n, 1000000008)
    if n > 500000004:
        c5 = 600000004 if (q ^ n) & 1 else 400000003
        n = 1000000008 - n
    else:
        c5 = 600000004 if q & 1 else 400000003
    m = n >> 1
    if m < 1024:
        a = _W[m]
        b = _W[m + 1]
    else:
        k = m >> (m.bit_length() - 10)
        a = _W[k]
        b = _W[k + 1]
        for c in bin(m)[12:]:
            if c == '1':
                a, b = (a * b - 3) % 1000000007, (b * b - 2) % 1000000007
            else:
                a, b = (a * a - 2) % 1000000007, (a * b - 3) % 1000000007
    if n & 1:
        return (a + b) * c5 % 1000000007
    return (2 * b - 3 * a) * c5 % 1000000007
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
