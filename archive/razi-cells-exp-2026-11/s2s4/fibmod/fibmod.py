import sys

M = 1_000_000_007


def fib(n):
    # fast doubling, fewer modulo operations per bit
    a, b = 0, 1
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
    for line in sys.stdin:
        s = line.strip()
        if s:
            out.append(str(fib(int(s))))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
