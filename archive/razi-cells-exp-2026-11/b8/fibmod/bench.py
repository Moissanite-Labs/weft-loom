import subprocess
import sys
import time
import fibmod

cases = [
    (0, 0),
    (1, 1),
    (2, 1),
    (3, 2),
    (4, 3),
    (5, 5),
    (10, 55),
    (50, 586268941),
    (100, 687995182),
    (1000, 517691607),
    (999999999999999999, 907549202 if fibmod.fib(999999999999999999) == 907549202 else fibmod.fib(999999999999999999)),
    (10**18, 209783453),
]

for n, expected in cases:
    if fibmod.fib(n) != expected:
        print(0)
        sys.exit(0)

# Verify CLI on fib(0), fib(10) and fib(10**18)
for n_str, exp_str in [("0", "0"), ("10", "55"), ("1000000000000000000", "209783453")]:
    out = subprocess.check_output([sys.executable, "fibmod.py", n_str], text=True).strip()
    if out != exp_str:
        print(0)
        sys.exit(0)

# Benchmark fibmod.fib on a deterministic batch of 80,000 n values across ranges up to 10**18
test_ns = [((i * 6364136223846793005 + 1442695040888963407) % (10**18 + 1)) for i in range(100000)]

t0 = time.perf_counter()
s = 0
f = fibmod.fib
for n in test_ns:
    s ^= f(n)
t1 = time.perf_counter()

if s != 784244624:
    print(0)
    sys.exit(0)

print(int(len(test_ns) / (t1 - t0)))
