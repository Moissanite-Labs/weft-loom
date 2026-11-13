import sys
def count_primes(n):
    if n < 3: return 0
    import numpy as np
    size = n // 2
    s = np.ones(size, dtype=np.bool_)
    s[0] = False
    r = int(n ** 0.5)
    for i in range(1, r // 2 + 1):
        if s[i]:
            p = 2 * i + 1
            s[p * p // 2::p] = False
    return int(np.count_nonzero(s)) + 1
print(count_primes(int(sys.argv[1])))
