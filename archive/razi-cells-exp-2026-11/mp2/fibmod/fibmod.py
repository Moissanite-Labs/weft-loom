import sys

MOD = 1_000_000_007


def fib_pair(n):
    # fast doubling: returns (F(n), F(n+1)) mod MOD
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = (a * ((2 * b - a) % MOD)) % MOD
        d = (a * a + b * b) % MOD
        if bit == '1':
            a, b = d, (c + d) % MOD
        else:
            a, b = c, d
    return a


def main():
    data = sys.stdin.read().split()
    out = []
    for tok in data:
        n = int(tok)
        out.append(str(fib_pair(n)))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
