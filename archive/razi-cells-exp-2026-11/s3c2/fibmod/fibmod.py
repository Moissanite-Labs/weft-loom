import sys
M = 1000000007
P = 2 * (M + 1)  # Pisano period for 1e9+7 divides 2(p+1)
BITS = 11
SZ = 1 << BITS
MASK = SZ - 1
K = 3  # n % P < 2**31 <= 2**33 = K * BITS


def mul(A, B):
    a, b, c, d = A
    e, f, g, h = B
    return ((a * e + b * g) % M, (a * f + b * h) % M,
            (c * e + d * g) % M, (c * f + d * h) % M)


# tables[i][d] = Q^(d * 2^(BITS*i)), Q = [[1,1],[1,0]]
ID = (1, 0, 0, 1)
tables = []
base = (1, 1, 1, 0)
for _ in range(K):
    t = [ID] * SZ
    cur = ID
    for d in range(1, SZ):
        cur = mul(cur, base)
        t[d] = cur
    tables.append(t)
    base = mul(cur, base)  # base^SZ


def fib(n):
    n %= P
    r = ID
    i = 0
    while n:
        d = n & MASK
        if d:
            r = mul(r, tables[i][d])
        n >>= BITS
        i += 1
    return r[1]


def main():
    out = []
    cache = {}
    for l in sys.stdin.read().split():
        n = int(l) % P
        r = cache.get(n)
        if r is None:
            r = cache[n] = fib(n)
        out.append(r)
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
