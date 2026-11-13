import sys
M = int(sys.argv[2]) if len(sys.argv) > 2 else 30
SP = [q for q in (2, 3, 5, 7) if M % q == 0]
R = [r for r in range(1, M) if all(r % q for q in SP)]
INV = {r: pow(r, -1, M) for r in R}
def count(n):
    if n < 2: return 0
    if n < 2000:
        return sum(1 for x in range(2, n) if all(x % d for d in range(2, int(x**0.5) + 1)))
    A = [bytearray([1]) * ((n - 1 - r) // M + 1) for r in R]
    A[0][0] = 0
    lim = int(n ** 0.5) + 1
    k = 0
    while True:
        base = M * k
        if base + R[0] > lim: break
        for j, r in enumerate(R):
            p = base + r
            if p < 7 or p > lim: continue
            if A[j][k]:
                ip = INV[r]
                for jj, rj in enumerate(R):
                    a = A[jj]
                    L = len(a)
                    mr = (rj * ip) % M
                    m0 = p + ((mr - p) % M)
                    k0 = (p * m0) // M
                    if k0 < L:
                        a[k0::p] = bytes(len(range(k0, L, p)))
        k += 1
    return sum(a.count(1) for a in A) + sum(1 for q in SP if q < n)
print(count(int(sys.argv[1])))
