import sys

MOD = 1_000_000_007


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
    data = sys.stdin.read().split()
    if not data:
        return
    out = [str(fib_mod(int(s))) for s in data]
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
