import sys

MOD = 1_000_000_007


def fib_mod(n):
    # Fast doubling: returns F(n) mod MOD
    a, b = 0, 1
    M = MOD
    for bit in bin(n)[2:]:
        c = a * (2 * b - a) % M
        d = (a * a + b * b) % M
        if bit == '1':
            a, b = d, (c + d) % M
        else:
            a, b = c, d
    return a


def main():
    data = sys.stdin.read().split()
    cache = {}
    out = []
    for s in data:
        n = int(s)
        r = cache.get(n)
        if r is None:
            r = fib_mod(n)
            cache[n] = r
        out.append(r)
    if out:
        sys.stdout.write("\n".join(map(str, out)) + "\n")


if __name__ == "__main__":
    main()
