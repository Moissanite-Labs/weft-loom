import sys
M = 1000000007
P = 2 * (M + 1)  # Pisano period of M divides P since M % 5 == 2

def mm(x, y):
    a, b, c, d = x
    e, f, g, h = y
    return ((a * e + b * g) % M, (a * f + b * h) % M,
            (c * e + d * g) % M, (c * f + d * h) % M)

# T[i][v] = Q^(v * 256**i), Q = [[1,1],[1,0]]; all powers of Q commute.
I = (1, 0, 0, 1)
T = []
unit = (1, 1, 1, 0)
for i in range(4):
    row = [I]
    for v in range(1, 256):
        row.append(mm(row[-1], unit))
    T.append(row)
    unit = mm(row[255], unit)

def fib(n):
    n %= P
    r = mm(mm(mm(T[0][n & 255], T[1][(n >> 8) & 255]), T[2][(n >> 16) & 255]), T[3][(n >> 24) & 255])
    return r[1]

def main():
    d = sys.stdin.read().split()
    c = {}
    out = []
    for s in d:
        r = c.get(s)
        if r is None:
            r = c[s] = fib(int(s))
        out.append(r)
    sys.stdout.write("\n".join(map(str, out)) + ("\n" if out else ""))
main()
