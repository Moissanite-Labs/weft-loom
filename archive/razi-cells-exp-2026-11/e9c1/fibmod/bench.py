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

test_ns = [0, 1, 2, 3, 5, 10, 50, 123456, 10**15 + 37, 10**18 - 1, 10**18]

# Verify CLI on key values
for n in [0, 1, 10, 10**18]:
    out = subprocess.check_output([sys.executable, "fibmod.py", str(n)], text=True).strip()
    if int(out) != ref_fib(n):
        print(0)
        sys.exit(0)

# Verify function on all test_ns
for n in test_ns:
    if fibmod.fib(n) != ref_fib(n):
        print(0)
        sys.exit(0)

# Benchmark
bench_ns = [10**18 - i * 9876543210123 for i in range(1000)]
f = fibmod.fib
t0 = time.perf_counter()
for _ in range(100):
    for n in bench_ns:
        f(n)
dt = time.perf_counter() - t0
print(f"{100000 / dt:.1f}")
