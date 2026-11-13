import sys
M = 1000000007
n = int(sys.argv[1])
a, b = 0, 1
for i in range(n.bit_length() - 1, -1, -1):
    c = a * (b + b - a) % M
    d = (a * a + b * b) % M
    if (n >> i) & 1:
        e = c + d
        if e >= M:
            e -= M
        a, b = d, e
    else:
        a, b = c, d
print(a)
