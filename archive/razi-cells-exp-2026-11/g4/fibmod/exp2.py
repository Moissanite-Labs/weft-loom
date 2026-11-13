import time, random
MOD = 1000000007
PER = 2000000016

def ref(n):
    n %= PER
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * ((b + b - a) % MOD) % MOD
        d = (a * a + b * b) % MOD
        if bit == '0': a, b = c, d
        else: a, b = d, (c + d) % MOD
    return a

def fd(n):
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * ((b + b - a) % MOD) % MOD
        d = (a * a + b * b) % MOD
        if bit == '0': a, b = c, d
        else: a, b = d, (c + d) % MOD
    return a, b

def build(L):
    # table A: (F(r), F(r+1)) for r in [0, 2^L)
    nA = 1 << L
    A0 = [0]*nA; A1 = [1]*nA
    x, y = 0, 1
    for i in range(1, nA):
        x, y = y, x + y
        if y >= MOD: y -= MOD
        A0[i] = x; A1[i] = y
    # table B: (F(q*s), F(q*s-1)) for q covering n < PER
    s = 1 << L
    Fs, Fs1 = fd(s)
    Fsm1 = Fs1 - Fs
    nB = (PER - 1 >> L) + 2
    B0 = [0]*nB; B1 = [0]*nB
    p, q_ = 0, 1   # F(0), F(1)
    for k in range(nB):
        B0[k] = p
        B1[k] = (q_ - p) % MOD
        p, q_ = (p*Fsm1 + q_*Fs) % MOD, (p*Fs + q_*Fs1) % MOD
    return (A0, A1, B0, B1), nA + nB

def mkfib(tab, L):
    A0, A1, B0, B1 = tab
    mask = (1 << L) - 1
    sh = L
    M = MOD; P = PER
    def fib(n, A0=A0, A1=A1, B0=B0, B1=B1, mask=mask, sh=sh, M=M, P=P):
        n %= P
        r = n & mask
        q = n >> sh
        return (A1[r]*B0[q] + A0[r]*B1[q]) % M
    return fib

ns = [random.randrange(10**18) for _ in range(200000)]
check = [ref(n) for n in ns[:3000]]

for L in (11, 12, 13, 14, 15, 16):
    t0 = time.perf_counter()
    tab, sz = build(L)
    tb = time.perf_counter() - t0
    f = mkfib(tab, L)
    ok = all(f(n) == c for n, c in zip(ns[:3000], check))
    best = 1e9
    s = 0
    for _ in range(3):
        t0 = time.perf_counter()
        for n in ns: s += f(n)
        best = min(best, time.perf_counter() - t0)
    print("L=%2d build %.3fs entries %8d ok=%s  %.3fs/200k -> %.0f calls/s (chk %d)" % (L, tb, sz, ok, best, 200000/best, s % MOD))
