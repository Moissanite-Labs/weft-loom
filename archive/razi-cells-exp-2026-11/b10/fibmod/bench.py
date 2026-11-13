import subprocess
import sys
import time
import fibmod

MOD = 1_000_000_007

def ref_fib(n):
    a, b = 0, 1
    for i in range(n.bit_length() - 1, -1, -1):
        c = a * ((b << 1) - a) % MOD
        d = (a * a + b * b) % MOD
        if (n >> i) & 1:
            a, b = d, (c + d) % MOD
        else:
            a, b = c, d
    return a

# Verify CLI once
out = subprocess.check_output([sys.executable, "fibmod.py", "10"], text=True).strip()
if out != "55":
    print(0)
    sys.exit(0)
out2 = subprocess.check_output([sys.executable, "fibmod.py", "1000000000000000000"], text=True).strip()
if out2 != str(ref_fib(10**18)):
    print(0)
    sys.exit(0)

# Verify edge cases and sample values
test_ns = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 100, 999999, 10**9, 10**18 - 1, 10**18]
for n in test_ns:
    if fibmod.fib(n) != ref_fib(n):
        print(0)
        sys.exit(0)

# Benchmark
f = fibmod.fib
N = 50000
inputs = [10**18 - i * 1337 for i in range(1000)]

# Warmup
for x in inputs:
    f(x)

t0 = time.perf_counter()
for _ in range(N // 1000):
    for x in inputs:
        f(x)
dt = time.perf_counter() - t0

print(int(N / dt))
