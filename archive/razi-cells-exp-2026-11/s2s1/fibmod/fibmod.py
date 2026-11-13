import sys

M = 1_000_000_007


def fib(n):
    # fast doubling: a = F(k), b = F(k+1)
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * ((2 * b - a) % M) % M      # F(2k)
        d = (a * a + b * b) % M            # F(2k+1)
        if bit == '1':
            a, b = d, (c + d) % M
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


main()
