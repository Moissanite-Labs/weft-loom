import subprocess
import sys
import time
import fibmod

MOD = 1_000_000_007

# Reference slow/simple check for small n and matrix exp for large n
def mat_mul(A, B):
    return (
        (A[0]*B[0] + A[1]*B[2]) % MOD,
        (A[0]*B[1] + A[1]*B[3]) % MOD,
        (A[2]*B[0] + A[3]*B[2]) % MOD,
        (A[2]*B[1] + A[3]*B[3]) % MOD,
    )

def ref_fib(n):
    if n <= 0:
        return 0
    res = (1, 0, 0, 1)
    base = (1, 1, 1, 0)
    while n > 0:
        if n & 1:
            res = mat_mul(res, base)
        base = mat_mul(base, base)
        n >>= 1
    return res[1]

test_cases = [0, 1, 2, 3, 5, 10, 20, 99, 100, 1000, 123456789, 10**15 + 37, 10**18 - 1, 10**18]
for tc in test_cases:
    if fibmod.fib(tc) != ref_fib(tc):
        print(0)
        sys.exit(0)

# Also check CLI for fib(10) and fib(10**18)
out10 = subprocess.check_output([sys.executable, "fibmod.py", "10"], text=True).strip()
out18 = subprocess.check_output([sys.executable, "fibmod.py", "1000000000000000000"], text=True).strip()
if out10 != "55" or out18 != str(ref_fib(10**18)):
    print(0)
    sys.exit(0)

# Benchmark fibmod.fib on a variety of 60-bit numbers
inputs = [((i * 6364136223846793005 + 1442695040888963407) & ((1 << 60) - 1)) for i in range(1000)]

# Warmup
f = fibmod.fib
for x in inputs:
    f(x)

iters = 100
t0 = time.perf_counter()
for _ in range(iters):
    for x in inputs:
        f(x)
dt = time.perf_counter() - t0
ops_per_sec = (iters * len(inputs)) / dt
print(int(ops_per_sec))
