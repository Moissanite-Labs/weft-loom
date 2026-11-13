import sys
M = 1000000007
Q = 2000000016
def fib_mod(n):
    n %= Q
    a, b = 0, 1
    for c in bin(n)[2:]:
        d = a * ((b << 1) - a) % M
        e = (a * a + b * b) % M
        if c == '0':
            a, b = d, e
        else:
            a, b = e, (d + e) % M
    return a
if __name__ == '__main__':
    n = int(sys.argv[1])
    if n < 0:
        m = -n
        v = fib_mod(m)
        if m % 2 == 0:
            v = (-v) % M
        print(v)
    else:
        print(fib_mod(n))
