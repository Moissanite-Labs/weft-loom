import sys, time
def cur(n):
    if n < 3: return 0
    size = n // 2
    sieve = bytearray([1]) * size
    sieve[0] = 0
    i = 1
    while True:
        p = 2*i+1; start = p*p//2
        if start >= size: break
        if sieve[i]:
            cnt = (size-1-start)//p + 1
            sieve[start::p] = bytes(cnt)
        i += 1
    return 1 + sieve.count(1)
def npv(n):
    import numpy as np
    if n < 3: return 0
    size = n // 2
    s = np.ones(size, dtype=np.bool_)
    s[0] = False
    i = 1
    while True:
        p = 2*i+1; start = p*p//2
        if start >= size: break
        if s[i]: s[start::p] = False
        i += 1
    return 1 + int(np.count_nonzero(s))
def w6(n):
    # residues 1 and 5 mod 6: a[k]=6k+1 (k>=1 .. ), b[k]=6k+5
    if n < 3: return 0
    if n < 4: return 1
    if n < 6: return 2
    la = (n - 2) // 6   # count of 6k+1 < n, k>=0 -> k < (n-1)/6 ; include k=0 (1), mark off
    la = (n - 1 + 5) // 6  # k in [0, la)
    lb = (n - 5 + 5) // 6  # 6k+5 < n -> k < (n-5)/6
    a = bytearray([1]) * la; b = bytearray([1]) * lb
    a[0] = 0
    lim = int(n ** 0.5) + 1
    for p in range(5, lim + 1):
        r = p % 6
        if r == 1:
            if not a[p // 6]: continue
        elif r == 5:
            if not b[p // 6]: continue
        else:
            continue
        # multiples of p that are 1 mod 6: p*m with m ≡ p^-1 (mod 6) i.e. m ≡ p mod 6 (since p^2≡1)
        # m ≡ p mod 6 -> product ≡ 1 mod 6 -> array a; m ≡ -p mod 6 -> array b
        pp = p * p
        # start at m=p (product p*p ≡ 1 mod 6) -> a; step 6p
        s = pp // 6
        if s < la: a[s::p] = bytes((la - 1 - s) // p + 1)
        # product ≡ 5 mod 6: m ≡ 5p mod 6; smallest m>=p: p + (5p - p) % 6 ... m = p + ((5*p - p) % 6)
        m = p + ((4 * p) % 6)
        s = (p * m) // 6
        if s < lb: b[s::p] = bytes((lb - 1 - s) // p + 1)
    return 2 + a.count(1) + b.count(1)
for f in (cur, npv, w6):
    try:
        ok = [f(2), f(3), f(10), f(100), f(5000000)]
        t = time.perf_counter(); r = f(100000000); dt = time.perf_counter() - t
        print(f.__name__, ok, r, round(dt, 3))
    except Exception as e:
        print(f.__name__, "ERR", e)
