import sys
M = 1000000007
P = 2 * (M + 1)
S = 1 << 16
F = [0, 1]
a, b = 0, 1
for _ in range(S):
    a, b = b, (a + b) % M
    F.append(b)
# F[k]=fib(k), k<=S+1
fS, fS1, fSm = F[S], F[S + 1], F[S - 1]
H = (P >> 16) + 2
X = [0] * H
Y = [0] * H  # fib(h*S), fib(h*S-1)
Y[0] = 1  # fib(-1)=1
x, y = 0, 1
for h in range(1, H):
    x, y = (x * fS1 + y * fS) % M, (x * fS + y * fSm) % M
    X[h] = x
    Y[h] = y
data = sys.stdin.buffer.read().split()
memo = {}
out = []
for t in data:
    r = memo.get(t)
    if r is None:
        n = int(t) % P
        h = n >> 16
        l = n & 65535
        r = memo[t] = (X[h] * F[l + 1] + Y[h] * F[l]) % M
    out.append(r)
sys.stdout.write("\n".join(map(str, out)) + "\n" if out else "")
