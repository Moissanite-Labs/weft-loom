import sys

MOD = 1_000_000_007
PERIOD = 2 * (MOD + 1)  # Pisano period divides 2(p+1) since p = 2 mod 5


def fib_mod(n):
    n %= PERIOD
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * ((2 * b - a) % MOD) % MOD
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
        out.append(str(fib_mod(int(s))))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
