import sys

M = 1_000_000_007
WINDOWS = 8  # n < 2**64 covers 10**18; 8 byte-sized windows


def _mul(x, y):
    a, b, c, d = x
    e, f, g, h = y
    return ((a * e + b * g) % M, (a * f + b * h) % M,
            (c * e + d * g) % M, (c * f + d * h) % M)


def _build():
    # T[p][d] = Q^(d * 256**p), Q = [[1,1],[1,0]]; Q^k top-right entry is F(k)
    ident = (1, 0, 0, 1)
    base = (1, 1, 1, 0)
    tables = []
    for _ in range(WINDOWS):
        row = [ident]
        for _d in range(255):
            row.append(_mul(row[-1], base))
        tables.append(row)
        base = _mul(row[255], base)  # base = Q^(256**(p+1))
    return tables


TABLES = _build()


def fib(n):
    r = (1, 0, 0, 1)
    p = 0
    while n:
        d = n & 255
        if d:
            r = _mul(r, TABLES[p][d])
        n >>= 8
        p += 1
    return r[1]


def main():
    out = []
    for line in sys.stdin:
        s = line.strip()
        if s:
            out.append(str(fib(int(s))))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
