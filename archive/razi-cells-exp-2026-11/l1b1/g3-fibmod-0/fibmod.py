import sys

M = 10**9 + 7
P = 2 * (M + 1)


def fib(n):
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * ((2 * b - a) % M) % M
        d = (a * a + b * b) % M
        if bit == '1':
            a, b = d, (c + d) % M
        else:
            a, b = c, d
    return a


def main():
    memo = {}
    out = []
    for tok in sys.stdin.buffer.read().split():
        r = memo.get(tok)
        if r is None:
            r = fib(int(tok) % P)
            memo[tok] = r
        out.append(r)
    if out:
        sys.stdout.write('\n'.join(map(str, out)) + '\n')


main()
