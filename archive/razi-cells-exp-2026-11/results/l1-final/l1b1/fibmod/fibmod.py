import sys
M = 1000000007
P = 2 * (M + 1)
K = 1 << 16
def main():
    toks = sys.stdin.buffer.read().split()
    memo = {}
    vals = []
    for tk in toks:
        if tk not in memo:
            memo[tk] = int(tk) % P
    mx = max(memo.values()) if memo else 0
    lo = [0, 1]
    a, b = 0, 1
    for _ in range(K):
        a, b = b, (a + b) % M
        lo.append(b)
    # lo[i]=F(i), i<=K+1
    FK, FK1, FKm = lo[K], lo[K + 1], lo[K - 1]
    H = mx >> 16
    h0 = [0]; h1 = [1]  # F(jK), F(jK-1)
    x, y = 0, 1
    for _ in range(H):
        x, y = (x * FK1 + y * FK) % M, (x * FK + y * FKm) % M
        h0.append(x); h1.append(y)
    # F(jK+b)=F(jK)F(b+1)+F(jK-1)F(b)
    res = {}
    for tk, n in memo.items():
        j = n >> 16; b = n & 65535
        res[tk] = (h0[j] * lo[b + 1] + h1[j] * lo[b]) % M
    sys.stdout.write("\n".join([str(res[t]) for t in toks]) + "\n")
main()
