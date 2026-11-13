import subprocess
import sys
import time
import fibmod

# Verify CLI correctness
out10 = subprocess.check_output([sys.executable, "fibmod.py", "10"]).strip()
out1e18 = subprocess.check_output([sys.executable, "fibmod.py", "1000000000000000000"]).strip()
if out10 != b"55" or out1e18 != b"209783453":
    print(0)
    sys.exit(0)

# Verify edge cases and identities via function or module execution
expected = {
    0: 0,
    1: 1,
    2: 1,
    3: 2,
    10: 55,
    50: 586268941,
    100: 687995182,
    10**18: 209783453,
}

# Benchmark
N_ITERS = 50000
test_ns = [0, 1, 2, 10, 50, 100, 123456789012345678, 999999999999999999, 10**18]

for n, exp in expected.items():
    if fibmod.fib(n) != exp:
        print(0)
        sys.exit(0)

t0 = time.perf_counter()
for _ in range(N_ITERS):
    for n in test_ns:
        fibmod.fib(n)
t1 = time.perf_counter()

elapsed = t1 - t0
print(int((N_ITERS * len(test_ns)) / elapsed))
