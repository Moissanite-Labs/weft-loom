import subprocess
import sys
import time
import fibmod

# Verify CLI
out = subprocess.check_output([sys.executable, "fibmod.py", "10"], text=True).strip()
if out != "55":
    print(0)
    sys.exit(0)

out2 = subprocess.check_output([sys.executable, "fibmod.py", "1000000000000000000"], text=True).strip()
if out2 != "209783453":
    print(0)
    sys.exit(0)

# Verify correctness across several values
expected = {
    0: 0,
    1: 1,
    2: 1,
    3: 2,
    10: 55,
    50: 586268941,
    100: 687995182,
    1000: 517691607,
    10**9: 21,
    10**18: 209783453,
}
for k, v in expected.items():
    if fibmod.fib(k) != v:
        print(0)
        sys.exit(0)

# Benchmark fib(n) for large values around 10**18
test_ns = [10**18 - i * 1234567890123 for i in range(1000)]
t0 = time.perf_counter()
iters = 200
for _ in range(iters):
    for n in test_ns:
        fibmod.fib(n)
elapsed = time.perf_counter() - t0
# Return ops per second
print(int(iters * len(test_ns) / elapsed))
