import sys
M = 1000000007
P = 2 * (M + 1)
def fib(n):
    n %= P
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
    data = sys.stdin.read().split()
    sys.stdout.write("\n".join(str(fib(int(x))) for x in data) + ("\n" if data else ""))
main()
