import sys

MOD = 1_000_000_007
PERIOD = 2 * (MOD + 1)  # Pisano period divides 2(p+1) since p == 2 mod 5


def fib_mod(n):
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * (2 * b - a) % MOD
        d = (a * a + b * b) % MOD
        if bit == '1':
            a = d
            b = (c + d) % MOD
        else:
            a = c
            b = d
    return a


def main():
    data = sys.stdin.buffer.read().split()
    cache = {}
    out = []
    for tok in data:
        n = int(tok) % PERIOD
        r = cache.get(n)
        if r is None:
            r = fib_mod(n)
            cache[n] = r
        out.append(r)
    sys.stdout.write("\n".join(map(str, out)) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
