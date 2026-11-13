import sys

M = 1_000_000_007
P = 2 * (M + 1)  # Pisano period of M divides 2(M+1) since M = 2 mod 5


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
    out = []
    app = out.append
    for s in sys.stdin.read().split():
        app(str(fib(int(s))))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
