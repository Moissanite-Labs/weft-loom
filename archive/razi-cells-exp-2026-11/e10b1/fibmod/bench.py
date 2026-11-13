import subprocess, sys, random, time
M = 1_000_000_007
def mat(n):
    def mul(X, Y):
        return [[(X[0][0]*Y[0][0]+X[0][1]*Y[1][0])%M, (X[0][0]*Y[0][1]+X[0][1]*Y[1][1])%M],
                [(X[1][0]*Y[0][0]+X[1][1]*Y[1][0])%M, (X[1][0]*Y[0][1]+X[1][1]*Y[1][1])%M]]
    R = [[1,0],[0,1]]; B = [[1,1],[1,0]]
    while n:
        if n & 1: R = mul(R, B)
        B = mul(B, B); n >>= 1
    return R[0][1]
def main():
    try:
        from fibmod import fib
        small = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        for i, v in enumerate(small):
            if fib(i) != v: return 0
        rng = random.Random(12345)
        ns = [rng.randrange(10**18 + 1) for _ in range(20000)]
        ns[0] = 10**18
        for n in ns[:300] + [rng.randrange(1, 10**6) for _ in range(100)]:
            if fib(n) != mat(n): return 0
        for n in (10, 10**18, ns[7]):
            out = subprocess.run([sys.executable, 'fibmod.py', str(n)], capture_output=True, text=True, timeout=10).stdout.strip()
            if out != str(mat(n)): return 0
        best = float('inf')
        acc_ref = None
        for _ in range(4):
            t = time.perf_counter()
            acc = 0
            for n in ns:
                acc ^= fib(n)
            best = min(best, time.perf_counter() - t)
            if acc_ref is None: acc_ref = acc
            elif acc != acc_ref: return 0
        return len(ns) / best
    except Exception as e:
        sys.stderr.write(repr(e) + '\n')
        return 0
print('%.1f' % main())
