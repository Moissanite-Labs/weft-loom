import sys


def main():
    M = 10**9 + 7
    P = 2 * (M + 1)  # multiple of the Pisano period of M (M = 2 mod 5)
    out = []
    for tok in sys.stdin.read().split():
        n = int(tok) % P
        a, b = 0, 1  # (F(k), F(k+1)) with k = 0
        for c in bin(n)[2:]:
            c2 = a * ((2 * b - a) % M) % M  # F(2k)
            d = (a * a + b * b) % M         # F(2k+1)
            if c == '1':
                a, b = d, (c2 + d) % M
            else:
                a, b = c2, d
        out.append(a)
    if out:
        sys.stdout.write('\n'.join(map(str, out)) + '\n')


main()
