import sys

MOD = 1_000_000_007


def fib_mod(n):
    # Fast doubling over bits of n, one mod per reduced value, locals only.
    a, b = 0, 1
    M = MOD
    for bit in bin(n)[2:]:
        c = a * (2 * b - a) % M
        d = (a * a + b * b) % M
        if bit == '1':
            a = d
            b = (c + d) % M
        else:
            a = c
            b = d
    return a


def main():
    out = []
    app = out.append
    f = fib_mod
    for line in sys.stdin:
        s = line.strip()
        if s:
            app(str(f(int(s))))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
