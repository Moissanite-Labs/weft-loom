import sys
from math import isqrt
def count_primes(n):
    if n < 3: return 0
    size = n // 2
    if n <= 8:
        return [0,0,0,1,2,2,3,3,4][n]
    per = 105
    pat = bytearray(1 for _ in range(per))
    for q in (3,5,7):
        pat[q//2::q] = bytes(len(range(q//2, per, q)))
    sieve = pat * (size // per + 1)
    del sieve[size:]
    sieve[0] = 0
    for q in (3,5,7): sieve[q//2] = 1
    for i in range(5, isqrt(n)//2 + 1):
        if sieve[i]:
            p = 2*i+1
            start = p*p//2
            sieve[start::p] = bytes(len(range(start, size, p)))
    return sieve.count(1) + 1
print(count_primes(int(sys.argv[1])))
