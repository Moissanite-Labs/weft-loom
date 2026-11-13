import time
import subprocess
import sys
import fibmod

MOD = 1_000_000_007

# Verify correctness against known values and recurrence
def verify():
    # CLI check
    out = subprocess.check_output([sys.executable, "fibmod.py", "10"]).decode().strip()
    if out != "55":
        return False
    out2 = subprocess.check_output([sys.executable, "fibmod.py", "1000000000000000000"]).decode().strip()
    if out2 != "209783453":
        return False
    
    # Small values check
    a, b = 0, 1
    for i in range(100):
        if fibmod.fib_mod(i) != a:
            return False
        a, b = b, (a + b) % MOD
        
    # Large values recurrence check: fib(n+2) = fib(n+1) + fib(n)
    for n in [10**5, 10**9, 10**12, 10**15, 10**18 - 2, 987654321012345678]:
        f0 = fibmod.fib_mod(n)
        f1 = fibmod.fib_mod(n + 1)
        f2 = fibmod.fib_mod(n + 2)
        if (f0 + f1) % MOD != f2:
            return False
    return True

if not verify():
    print(0)
    sys.exit(0)

# Benchmark fibmod.fib_mod over many large inputs
inputs = [10**18 - i * 9876543210123 for i in range(50000)]

t0 = time.perf_counter()
s = 0
f = fibmod.fib_mod
for x in inputs:
    s += f(x)
t1 = time.perf_counter()

if s == 0:
    print(0)
else:
    ops_per_sec = len(inputs) / (t1 - t0)
    print(int(ops_per_sec))
