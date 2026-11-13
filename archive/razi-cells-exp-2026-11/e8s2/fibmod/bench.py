import subprocess
import sys
import time
import fibmod

MOD = 1_000_000_007

# Verify CLI
out = subprocess.check_output([sys.executable, "fibmod.py", "10"], text=True).strip()
if out != "55":
    print(0)
    sys.exit(0)

out2 = subprocess.check_output([sys.executable, "fibmod.py", "1000000000000000000"], text=True).strip()

# Reference fast doubling
def ref_fib(n):
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = (a * ((b * 2 - a) % MOD)) % MOD
        d = (a * a + b * b) % MOD
        if bit == '0':
            a, b = c, d
        else:
            a, b = d, (c + d) % MOD
    return a

test_cases = [0, 1, 2, 3, 5, 10, 50, 100, 1234567, 999999999999999999, 10**18]
for tc in test_cases:
    if fibmod.fib(tc) != ref_fib(tc):
        print(0)
        sys.exit(0)

if int(out2) != ref_fib(10**18):
    print(0)
    sys.exit(0)

# Benchmark fibmod.fib on a fixed set of 50,000 large numbers up to 10**18
nums = [(10**18 - i * 13333333333337) % (10**18 + 1) for i in range(50000)]

t0 = time.perf_counter()
s = 0
f = fibmod.fib
for n in nums:
    s += f(n)
elapsed = time.perf_counter() - t0
if s == -1:
    print(0)
else:
    print(int(50000 / elapsed))
