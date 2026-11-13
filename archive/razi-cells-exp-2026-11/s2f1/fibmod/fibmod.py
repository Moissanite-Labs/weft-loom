import sys

MOD = 1_000_000_007


def fib(n):
    # Fast doubling; state (a, b) = (F(k), F(k+1)), scanning bits of n MSB first.
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * ((2 * b - a) % MOD) % MOD  # F(2k)
        d = (a * a + b * b) % MOD          # F(2k+1)
        if bit == '1':
            a, b = d, (c + d) % MOD
        else:
            a, b = c, d
    return a


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
