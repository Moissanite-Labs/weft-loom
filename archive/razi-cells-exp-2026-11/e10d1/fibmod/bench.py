import time, random, sys
from fibmod import fib, M

# correctness check vs naive
a, b = 0, 1
for i in range(300):
    if fib(i) != a:
        print(0); sys.exit(0)
    a, b = b, (a + b) % M
if fib(10**18) != 209783453 or fib(10) != 55:
    print(0); sys.exit(0)

random.seed(1)
ns = [random.randrange(1, 10**18) for _ in range(2000)]
best = None
for _ in range(3):
    t = time.perf_counter()
    for _ in range(10):
        for n in ns:
            fib(n)
    dt = time.perf_counter() - t
    best = dt if best is None or dt < best else best
print(int(20000 / best))
