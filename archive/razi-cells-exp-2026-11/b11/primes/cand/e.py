import sys
from math import isqrt
def count_primes(n, PRE=(7,11,13)):
    if n < 3: return 0
    if n < 60:
        return sum(1 for k in range(2, n) if all(k % d for d in range(2, isqrt(k)+1)))
    M = 30
    R = (1,7,11,13,17,19,23,29)
    inv = {r: pow(r,-1,M) for r in R}
    sizes = [(n - r - 1)//M + 1 for r in R]
    per = 1
    for p in PRE: per *= p
    pats = [bytearray([1])*per for _ in R]
    for p in PRE:
        pinv = inv[p]
        for i, r in enumerate(R):
            q = (r*pinv) % M
            if q < p: q += M*((p-q+M-1)//M)
            s = (p*q - r)//M
            pats[i][s % p::p] = bytes(len(range(s%p, per, p)))
    arrs = []
    for i in range(8):
        a = pats[i]*(sizes[i]//per + 1); del a[sizes[i]:]; arrs.append(a)
    arrs[0][0] = 0
    for p in PRE:
        arrs[R.index(p)][0] = 1
    rt = isqrt(n)
    pmin = max(PRE)
    for k in range(0, rt//M + 1):
        base = M*k
        for i, r in enumerate(R):
            p = base + r
            if p <= pmin: continue
            if p > rt: break
            if not arrs[i][k]: continue
            pinv = inv[r]
            for j, rj in enumerate(R):
                q = (rj*pinv) % M
                if q < p: q += M*((p-q+M-1)//M)
                s = (p*q - rj)//M
                arrs[j][s::p] = bytes(len(range(s, sizes[j], p)))
    return 3 + sum(a.count(1) for a in arrs)
print(count_primes(int(sys.argv[1])))
