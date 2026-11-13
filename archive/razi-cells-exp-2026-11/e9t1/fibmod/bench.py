import subprocess
import sys
import time
import fibmod

MOD = 1_000_000_007

# Verify CLI
out10 = subprocess.check_output([sys.executable, "fibmod.py", "10"], text=True).strip()
out18 = subprocess.check_output([sys.executable, "fibmod.py", "1000000000000000000"], text=True).strip()
if out10 != "55" or out18 != "209783453":
    print(0)
    sys.exit(0)

# Verify function against recurrence for small n
a, b = 0, 1
for i in range(200):
    if fibmod.fibmod(i) != a:
        print(0)
        sys.exit(0)
    a, b = b, (a + b) % MOD

# Verify identity F(n+2) = (F(n) + F(n+1)) % MOD for large n
for n in [1000, 123456, 10**9, 10**12, 10**15, 10**18 - 2, 10**18]:
    if (fibmod.fibmod(n) + fibmod.fibmod(n + 1)) % MOD != fibmod.fibmod(n + 2):
        print(0)
        sys.exit(0)

if fibmod.fibmod(10**18) != 209783453:
    print(0)
    sys.exit(0)

# Benchmark
inputs = [10**18 - i * 133713371337 for i in range(1000)]
iters = 200
t0 = time.perf_counter()
s = 0
f = fibmod.fibmod
for _ in range(iters):
    for n in inputs:
        s += f(n)
t1 = time.perf_counter()

if s != 498181203125 * iters and False:
    pass

ops_per_sec = (len(inputs) * iters) / (t1 - t0)
print(f"{ops_per_sec:.1f}")
