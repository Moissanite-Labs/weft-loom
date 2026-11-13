import sys
M = 1000000007

def pair(n):
    # returns (F(n), F(n+1)) mod M, fast doubling (used once, to find the period)
    a, b = 0, 1
    for c in bin(n)[2:]:
        t = a * ((2 * b - a) % M) % M
        u = (a * a + b * b) % M
        if c == '1':
            a, b = u, (t + u) % M
        else:
            a, b = t, u
    return a, b

def _period():
    # Pisano period of M divides 2(M+1) since M = 2 (mod 5)
    N = 2 * (M + 1)
    fs = []
    x = N
    d = 2
    while d * d <= x:
        if x % d == 0:
            fs.append(d)
            while x % d == 0:
                x //= d
        d += 1
    if x > 1:
        fs.append(x)
    p = N
    for q in fs:
        while p % q == 0 and pair(p // q) == (0, 1):
            p //= q
    return p

PER = _period()  # < 2**31

# 2x2 matrices as tuples (a, b, c, d); Q^n = [[F(n+1), F(n)], [F(n), F(n-1)]]
def mul(x, y):
    a, b, c, d = x
    e, f, g, h = y
    return ((a * e + b * g) % M, (a * f + b * h) % M,
            (c * e + d * g) % M, (c * f + d * h) % M)

W = 2048  # 11-bit digits; three digits cover exponents below 2**33

def table(base):
    t = [(1, 0, 0, 1)]
    for _ in range(W - 1):
        t.append(mul(t[-1], base))
    return t

Q = (1, 1, 1, 0)
T0 = table(Q)                 # Q^d
B1 = mul(T0[-1], Q)           # Q^2048
T1 = table(B1)                # Q^(d*2048)
B2 = mul(T1[-1], B1)          # Q^(2048^2)
T2 = table(B2)                # Q^(d*2048^2)

def fib(n):
    n %= PER
    r = mul(mul(T0[n & 2047], T1[(n >> 11) & 2047]), T2[n >> 22])
    return r[1]

def main():
    cache = {}
    out = []
    for tok in sys.stdin.read().split():
        v = cache.get(tok)
        if v is None:
            v = fib(int(tok))
            cache[tok] = v
        out.append(str(v))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))

main()
