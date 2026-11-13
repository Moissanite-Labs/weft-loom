import sys

MOD = 1_000_000_007


def fib(n):
    # fast doubling, returns F(n) mod MOD
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = (a * ((2 * b - a) % MOD)) % MOD
        d = (a * a + b * b) % MOD
        if bit == "1":
            a, b = d, (c + d) % MOD
        else:
            a, b = c, d
    return a


def main():
    out = []
    for line in sys.stdin:
        s = line.strip()
        if not s:
            continue
        out.append(str(fib(int(s))))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
