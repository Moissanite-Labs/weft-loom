import sys
import numpy as np
from math import isqrt
def count_primes(n):
    if n < 3: return 0
    size = n//2
    s = np.ones(size, dtype=np.bool_)
    s[0] = False
    for i in range(1, isqrt(n)//2+1):
        if s[i]:
            p = 2*i+1
            s[p*p//2::p] = False
    return int(s.sum()) + 1
print(count_primes(int(sys.argv[1])))
