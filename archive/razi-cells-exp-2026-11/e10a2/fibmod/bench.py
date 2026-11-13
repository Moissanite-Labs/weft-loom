import subprocess, sys, time, random
M = 1000000007

def ref(n):
    # independent reference: 2x2 matrix power
    def mul(A, B):
        return ((A[0]*B[0] + A[1]*B[2]) % M, (A[0]*B[1] + A[1]*B[3]) % M,
                (A[2]*B[0] + A[3]*B[2]) % M, (A[2]*B[1] + A[3]*B[3]) % M)
    R = (1, 0, 0, 1); P = (1, 1, 1, 0)
    while n:
        if n & 1: R = mul(R, P)
        P = mul(P, P); n >>= 1
    return R[1]

def main():
    try:
        from fibmod import fib
        # small n against naive iteration
        a, b = 0, 1
        for i in range(500):
            if fib(i) != a: return 0
            a, b = b, (a + b) % M
        rnd = random.Random(12345)
        edge = [10**18, 10**18 - 1, 2**59, 2**59 - 1, 2**60 - 1, 1, 0, 2, 3]
        for n in edge + [rnd.randrange(10**18 + 1) for _ in range(1000)]:
            if fib(n) != ref(n): return 0
        # command-line interface check (the actual NEED)
        for n, want in [(10, 55), (0, 0), (1, 1), (10**18, ref(10**18)), (987654321987654321, ref(987654321987654321))]:
            out = subprocess.run([sys.executable, "fibmod.py", str(n)], capture_output=True, text=True, timeout=10)
            if out.returncode != 0 or out.stdout.strip() != str(want): return 0
        # timing: fixed workload of large n, CPU time, best of many short repeats
        ns = [rnd.randrange(10**17, 10**18 + 1) for _ in range(5000)]
        best = float("inf")
        for _ in range(31):
            t = time.process_time()
            for n in ns:
                fib(n)
            best = min(best, time.process_time() - t)
        return len(ns) / best
    except Exception:
        return 0

if __name__ == "__main__":
    print("%.1f" % main())
