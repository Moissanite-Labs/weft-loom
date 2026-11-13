import sys

M = 1_000_000_007
PER = 2 * (M + 1)
W = 11
MASK = (1 << W) - 1
NW = 3


def _mul(x, y):
    a, b, c = x
    d, e, f = y
    # symmetric matrices [[a,b],[b,c]] (powers of Q are symmetric)
    return ((a * d + b * e) % M, (a * e + b * f) % M, (b * e + c * f) % M)


def _build():
    base = (1, 1, 0)
    ident = (1, 0, 1)
    tables = []
    for _ in range(NW):
        row = [ident]
        for _d in range(MASK):
            row.append(_mul(row[-1], base))
        tables.append(row)
        base = _mul(row[MASK], base)
    return tables


T0, T1, T2 = _build()


def main():
    out = []
    for line in sys.stdin:
        s = line.strip()
        if s:
            n = int(s) % PER
            a, b, c = T0[n & MASK]
            d, e, f = T1[(n >> 11) & MASK]
            # F = off-diagonal of product; product P=(T0*T1)
            p0 = (a * d + b * e) % M
            p1 = (a * e + b * f) % M
            p2 = (b * e + c * f) % M
            g, h, i = T2[n >> 22]
            out.append((p0 * h + p1 * i) % M if False else (p1 * g + p2 * h) % M)
    if out:
        sys.stdout.write("\n".join(map(str, out)) + "\n")


if __name__ == "__main__":
    main()
