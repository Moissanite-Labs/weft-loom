import sys

M = 10**9 + 7


def fib(n):
    # fast doubling: a = F(k), b = F(k+1), start k = 0
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * ((2 * b - a) % M) % M  # F(2k)
        d = (a * a + b * b) % M        # F(2k+1)
        if bit == '1':
            a, b = d, (c + d) % M
        else:
            a, b = c, d
    return a


def main():
    out = [str(fib(int(tok))) for tok in sys.stdin.read().split()]
    if out:
        sys.stdout.write("\n".join(out) + "\n")


main()
