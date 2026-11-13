import sys

MOD = 1_000_000_007


def _mul(X, Y):
    a, b, c, d = X
    e, f, g, h = Y
    return ((a * e + b * g) % MOD, (a * f + b * h) % MOD,
            (c * e + d * g) % MOD, (c * f + d * h) % MOD)


I = (1, 0, 0, 1)

# P[k] = Q^(2^k), Q = [[1,1],[1,0]]
P = []
_q = (1, 1, 1, 0)
for _k in range(64):
    P.append(_q)
    _q = _mul(_q, _q)

# T[j][v] = Q^(v << 8j) for 8-bit chunks j = 0..7
T = []
for j in range(8):
    row = [I] * 256
    for v in range(1, 256):
        low = v & -v
        idx = low.bit_length() - 1
        row[v] = _mul(row[v ^ low], P[8 * j + idx])
    T.append(row)


def fib_mod(n):
    R = I
    for j in range(8):
        v = (n >> (8 * j)) & 255
        if v:
            R = _mul(R, T[j][v])
    return R[1]


def main():
    out = []
    cache = {}
    for line in sys.stdin:
        s = line.strip()
        if not s:
            continue
        n = int(s)
        r = cache.get(n)
        if r is None:
            r = fib_mod(n)
            if len(cache) < 100000:
                cache[n] = r
        out.append(r)
    sys.stdout.write("\n".join(map(str, out)))
    if out:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
