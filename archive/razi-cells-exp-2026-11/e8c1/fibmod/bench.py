import subprocess
import sys
import time
import fibmod

MOD = 1_000_000_007

# Check CLI once
out = subprocess.check_output([sys.executable, "fibmod.py", "10"], text=True).strip()
if out != "55":
    print(0)
    sys.exit(0)

out2 = subprocess.check_output([sys.executable, "fibmod.py", "1000000000000000000"], text=True).strip()

# Known values / reference check
def ref_fib(n):
    a, b = 0, 1
    for i in range(n.bit_length() - 1, -1, -1):
        c = (a * ((b << 1) - a)) % MOD
        d = (a * a + b * b) % MOD
        if (n >> i) & 1:
            a, b = d, (c + d) % MOD
        else:
            a, b = c, d
    return a

if out2 != str(ref_fib(10**18)):
    print(0)
    sys.exit(0)

test_ns = [0, 1, 2, 3, 5, 10, 100, 1234567, 10**9, 10**18, 999999999999999999, 2**60 - 1]
for n in test_ns:
    if fibmod.fib(n) != ref_fib(n):
        print(0)
        sys.exit(0)

# Benchmark loop (~0.5s)
ns = [10**18 - i * 1234567890123 for i in range(500)]
f = fibmod.fib
t0 = time.perf_counter()
for _ in range(400):
    for n in ns:
        f(n)
dt = time.perf_counter() - t0
print(int(200000 / dt))
