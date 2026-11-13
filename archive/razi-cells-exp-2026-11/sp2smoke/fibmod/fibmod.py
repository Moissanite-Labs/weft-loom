import sys

M = 10**9 + 7
P = 2 * (M + 1)  # Pisano period divides this, so reduce n first


def fib(n):
    n %= P
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * (2 * b - a) % M
        d = (a * a + b * b) % M
        if bit == '1':
            a, b = d, (c + d) % M
        else:
            a, b = c, d
    return a


def main():
    cache = {}
    out = []
    for s in sys.stdin.read().split():
        n = int(s)
        r = cache.get(n)
        if r is None:
            r = fib(n)
            cache[n] = r
        out.append(str(r))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


main()
