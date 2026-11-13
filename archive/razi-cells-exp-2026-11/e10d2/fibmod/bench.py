import time, random, subprocess, sys
from fibmod import fib, M

# correctness checks
a, b = 0, 1
ref = {}
for i in range(2000):
    ref[i] = a
    a, b = b, (a + b) % M
for i in [0, 1, 2, 10, 50, 99, 1000, 1999]:
    assert fib(i) == ref[i], i
assert fib(10**18) == 209783453
assert fib(123456789012345678) == fib(123456789012345678)  # determinism
out = subprocess.run([sys.executable, "fibmod.py", "10"], capture_output=True, text=True).stdout.strip()
assert out == "55", out

random.seed(1)
ns = [random.randrange(10**17, 10**18) for _ in range(10000)]
best = 0.0
for rep in range(7):
    t = time.perf_counter()
    s = 0
    for n in ns:
        s ^= fib(n)
    dt = time.perf_counter() - t
    best = max(best, len(ns) / dt)
print(best)
