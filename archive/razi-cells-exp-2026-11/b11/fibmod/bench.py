import time, sys, random
from fibmod import fib
M = 1_000_000_007
# correctness checks
def slow(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, (a + b) % M
    return a
for n in [0, 1, 2, 10, 100, 1000, 12345]:
    if fib(n) != slow(n): print(0); sys.exit(0)
if fib(10**18) != 209783453: print(0); sys.exit(0)
rng = random.Random(1)
ns = [rng.randrange(10**17, 10**18) for _ in range(2000)]
t = time.perf_counter()
for _ in range(10):
    for n in ns: fib(n)
dt = time.perf_counter() - t
print(20000 / dt)
