import sys, time, math, importlib
sys.path.insert(0, '.')
import primes

# Correctness checks, including the required value.
def ref(n):
    return sum(1 for x in range(2, min(n, 10000)) if all(x % d for d in range(2, math.isqrt(x) + 1)))
for n in [0, 1, 2, 3, 4, 5, 10, 100, 1000, 7919, 10000, 100000, 5000000]:
    got = primes.count(n)
    if n <= 10000:
        exp = ref(n)
    elif n == 100000:
        exp = 9592
    elif n == 5000000:
        exp = 348513
    else:
        exp = None
    if exp is not None and got != exp:
        print(0)
        sys.exit(0)
if primes.count(5000000) != 348513:
    print(0)
    sys.exit(0)
N = 5000000
reps = 0
t0 = time.perf_counter()
while time.perf_counter() - t0 < 0.7:
    for _ in range(4):
        if primes.count(N) != 348513:
            print(0); sys.exit(0)
    reps += 4
dt = time.perf_counter() - t0
print(reps / dt)
