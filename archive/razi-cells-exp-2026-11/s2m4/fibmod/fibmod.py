import sys

MOD = 1_000_000_007


def fib_pair(n):
    # returns (F(n), F(n+1)) mod MOD via fast doubling, iterating over bits of n
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
    out = []
    for line in sys.stdin:
        s = line.strip()
        if not s:
            continue
        out.append(str(fib_pair(int(s))))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
