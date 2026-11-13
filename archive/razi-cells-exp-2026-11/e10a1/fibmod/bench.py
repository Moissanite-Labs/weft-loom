import subprocess, sys, time, random
M = 1_000_000_007
def mat(n):
    def mul(A, B):
        return [[(A[0][0]*B[0][0]+A[0][1]*B[1][0]) % M, (A[0][0]*B[0][1]+A[0][1]*B[1][1]) % M],
                [(A[1][0]*B[0][0]+A[1][1]*B[1][0]) % M, (A[1][0]*B[0][1]+A[1][1]*B[1][1]) % M]]
    R = [[1, 0], [0, 1]]; P = [[1, 1], [1, 0]]
    while n:
        if n & 1: R = mul(R, P)
        P = mul(P, P); n >>= 1
    return R[0][1]
def naive(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, (a+b) % M
    return a

def main():
    sys.path.insert(0, '.')
    import fibmod
    # correctness: small n vs naive, large n vs matrix reference
    for n in range(0, 200):
        if fibmod.fib(n) != naive(n): return 0
    rnd = random.Random(12345)
    tests = [10**18, 10**18-1, 2**59, 2**59-1, 999999999999, 123456789012345678]
    tests += [rnd.randrange(10**18) for _ in range(200)]
    tests += [rnd.randrange(10**k) for k in range(1, 18) for _ in range(5)]
    for n in tests:
        if fibmod.fib(n) != mat(n): return 0
    # CLI check
    for n in [0, 1, 10, 10**18, 987654321987654321]:
        out = subprocess.run([sys.executable, 'fibmod.py', str(n)], capture_output=True, text=True).stdout.strip()
        if out != str(mat(n)): return 0
    # timing: fixed workload of large n, best of 5 rounds
    work = [rnd.randrange(10**17, 10**18) for _ in range(4000)] + [10**18]
    f = fibmod.fib
    best = float('inf')
    for _ in range(5):
        t = time.perf_counter()
        for n in work: f(n)
        best = min(best, time.perf_counter() - t)
    return len(work) / best

if __name__ == "__main__":
    try:
        print(round(main(), 1))
    except Exception:
        print(0)
