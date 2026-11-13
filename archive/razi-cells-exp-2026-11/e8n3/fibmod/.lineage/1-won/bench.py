import subprocess
import sys
import time
import random
import fibmod

# 1. Verify CLI behavior
cli_tests = [
    (0, 0),
    (1, 1),
    (2, 1),
    (10, 55),
    (50, 586268941),
    (10**18, 209783453),
]
for n, expected in cli_tests:
    out = subprocess.check_output([sys.executable, "fibmod.py", str(n)], text=True).strip()
    if int(out) != expected:
        print(0)
        sys.exit(0)

# 2. Verify fib(n) function across many test cases
MOD = 1_000_000_007
a, b = 0, 1
for i in range(200):
    if fibmod.fib(i) != a:
        print(0)
        sys.exit(0)
    a, b = b, (a + b) % MOD

for n, expected in cli_tests:
    if fibmod.fib(n) != expected:
        print(0)
        sys.exit(0)

# 3. Benchmark fibmod.fib(n) for large n up to 10**18
rng = random.Random(42)
inputs = [rng.randint(0, 10**18) for _ in range(100_000)]

def ref_fib(n):
    if n == 0:
        return 0
    a, b = 0, 1
    for bit in range(n.bit_length() - 1, -1, -1):
        c = (a * ((b << 1) - a)) % MOD
        d = (a * a + b * b) % MOD
        if (n >> bit) & 1:
            a, b = d, (c + d) % MOD
        else:
            a, b = c, d
    return a

for x in inputs[:500]:
    if fibmod.fib(x) != ref_fib(x):
        print(0)
        sys.exit(0)

f = fibmod.fib
# Warmup
for x in inputs[:1000]:
    f(x)

t0 = time.perf_counter()
s = 0
for x in inputs:
    s += f(x)
t1 = time.perf_counter()

if s != 50043435986647:
    print(0)
    sys.exit(0)

ops_per_sec = len(inputs) / (t1 - t0)
print(f"{ops_per_sec:.1f}")
