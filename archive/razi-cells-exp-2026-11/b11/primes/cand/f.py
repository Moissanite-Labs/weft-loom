import sys
from math import isqrt
def count_primes(n, PRE=(5,7,11,13)):
    if n < 3: return 0
    if n < 200:
        return sum(1 for k in range(2, n) if all(k % d for d in range(2, isqrt(k)+1)))
    sizes = {1:(n-2)//6+1, 5:(n-6)//6+1}
    per = 1
    for p in PRE: per *= p
    pats = {1: bytearray([1])*per, 5: bytearray([1])*per}
    for p in PRE:
        for r in (1,5):
            q = r if p % 6 == 1 else (5*r) % 6
            s = (p*q - r)//6
            pats[r][s % p::p] = bytes(len(range(s % p, per, p)))
    arrs = {}
    for r in (1,5):
        a = pats[r]*(sizes[r]//per+1); del a[sizes[r]:]; arrs[r] = a
    A = arrs[1]; B = arrs[5]; sa = sizes[1]; sb = sizes[5]
    A[0] = 0
    for p in PRE: arrs[p % 6][(p - p % 6)//6] = 1
    rt = isqrt(n)
    for p in range(max(PRE)+2, rt+1, 2):
        m = p % 6
        if m == 1:
            if not A[(p-1)//6]: continue
            s = (p*p-1)//6
            A[s::p] = bytes(len(range(s, sa, p)))
            s = (p*(p+4)-5)//6
            B[s::p] = bytes(len(range(s, sb, p)))
        elif m == 5:
            if not B[(p-5)//6]: continue
            s = (p*p-1)//6
            A[s::p] = bytes(len(range(s, sa, p)))
            s = (p*(p+2)-5)//6
            B[s::p] = bytes(len(range(s, sb, p)))
    return 2 + A.count(1) + B.count(1)
print(count_primes(int(sys.argv[1])))
