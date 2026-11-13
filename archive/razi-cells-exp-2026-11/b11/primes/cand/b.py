import sys
from math import isqrt
def count_primes(n):
    if n < 3: return 0
    if n < 4: return 1
    if n < 6: return 2
    sa = (n-2)//6 + 1
    sb = (n-6)//6 + 1
    A = bytearray([1]) * sa
    B = bytearray([1]) * sb
    A[0] = 0
    r = isqrt(n)
    for p in range(5, r+1, 2):
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
