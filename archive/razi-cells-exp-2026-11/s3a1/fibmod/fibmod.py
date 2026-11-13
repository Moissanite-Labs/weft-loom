import sys

MOD = 1_000_000_007


def fib(n):
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
    w = sys.stdout.write
    out = []
    app = out.append
    for line in sys.stdin:
        s = line.strip()
        if s:
            app(str(fib(int(s))))
    if out:
        w("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
