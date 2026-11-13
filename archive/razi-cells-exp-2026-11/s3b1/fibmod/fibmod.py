import sys
M = 1000000007
P = 2000000016
def fib(n):
    a, b = 0, 1
    for i in range(n.bit_length() - 1, -1, -1):
        c = a * (2 * b - a) % M
        d = (a * a + b * b) % M
        if (n >> i) & 1:
            a, b = d, (c + d) % M
        else:
            a, b = c, d
    return a
data = sys.stdin.read().split()
cache = {}
out = []
for t in data:
    n = int(t) % P
    r = cache.get(n)
    if r is None:
        r = cache[n] = fib(n)
    out.append(r)
print("\n".join(map(str, out)))
