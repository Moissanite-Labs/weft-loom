import sys

M = 1000000007


def fib(n):
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
    data = sys.stdin.read().split()
    if data:
        sys.stdout.write("\n".join(str(fib(int(s))) for s in data) + "\n")


if __name__ == "__main__":
    main()
