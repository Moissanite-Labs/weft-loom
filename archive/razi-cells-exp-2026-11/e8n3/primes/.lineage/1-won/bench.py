import subprocess, sys, time

# Verify CLI output first
out = subprocess.check_output([sys.executable, "primes.py", "5000000"]).decode().strip()
if out != "348513":
    print(0)
    sys.exit(0)

import primes

# Verify correctness across several cases
cases = [
    (0, 0), (1, 0), (2, 0), (3, 1), (4, 2), (5, 2), (6, 3),
    (10, 4), (11, 4), (12, 5), (100, 25), (1000, 168),
    (5000000, 348513), (50000000, 3001134), (100000000, 5761455)
]
for n, exp in cases:
    if primes.count_primes(n) != exp:
        print(0)
        sys.exit(0)

# Benchmark heavy workload (~0.3-1.0s initially)
t0 = time.perf_counter()
iters = 0
while True:
    primes.count_primes(5000000)
    primes.count_primes(50000000)
    primes.count_primes(100000000)
    iters += 1
    dt = time.perf_counter() - t0
    if dt >= 0.4:
        break

score = iters / dt
print(f"{score:.2f}")
