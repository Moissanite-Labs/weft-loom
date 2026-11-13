import sys

M = 1_000_000_007
P = 2 * (M + 1)  # Pisano period of M


def mul(x, y):
    a, b, c, d = x
    e, f, g, h = y
    return ((a * e + b * g) % M, (a * f + b * h) % M,
            (c * e + d * g) % M, (c * f + d * h) % M)


# T[k][v] = Q^(v * 256^k), Q = [[1,1],[1,0]] as flat tuples (a,b,c,d)
Q = (1, 1, 1, 0)
I = (1, 0, 0, 1)
T = []
base = Q  # Q^(256^k)
for k in range(4):
    row = [I]
    for v in range(1, 256):
        row.append(mul(row[-1], base))
    T.append(row)
    base = mul(row[255], base)  # base^256 = Q^(256^(k+1))


def fib(n):
    n %= P
    r = I
    for k in range(4):
        v = (n >> (8 * k)) & 255
        if v:
            r = mul(r, T[k][v])
    return r[1]  # Q^n = [[F(n+1),F(n)],[F(n),F(n-1)]]


def main():
    out = []
    cache = {}
    for line in sys.stdin:
        s = line.strip()
        if not s:
            continue
        if s not in cache:
            cache[s] = str(fib(int(s)))
        out.append(cache[s])
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
