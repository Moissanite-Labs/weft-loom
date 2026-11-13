import sys
from math import isqrt
def count_primes(n):
    if n < 3: return 0
    if n < 4: return 1
    if n < 6: return 2
    sa = (n-2)//6 + 1
    sb = (n-6)//6 + 1
    # pre-sieve 5 and 7 via pattern (period 35 in k-space)
    per = 35
    pa = bytearray([1])*per; pb = bytearray([1])*per
    for p in (5,7):
        if p % 6 == 1:
            s=(p*p-1)//6; pa[s%p::p]=bytes(len(range(s%p,per,p)))
            s=(p*(p+4)-5)//6; pb[s%p::p]=bytes(len(range(s%p,per,p)))
        else:
            s=(p*p-1)//6; pa[s%p::p]=bytes(len(range(s%p,per,p)))
            s=(p*(p+2)-5)//6; pb[s%p::p]=bytes(len(range(s%p,per,p)))
    A = pa * (sa//per + 1); del A[sa:]
    B = pb * (sb//per + 1); del B[sb:]
    A[0] = 0; B[0] = 1; A[1] = 1
    r = isqrt(n)
    for p in range(11, r+1, 2):
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
