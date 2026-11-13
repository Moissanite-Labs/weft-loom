import subprocess, time, sys
import primes

CASES = [
    (0, 0),
    (1, 0),
    (2, 0),
    (3, 1),
    (4, 2),
    (5, 2),
    (6, 3),
    (10, 4),
    (11, 4),
    (12, 5),
    (30, 10),
    (100, 25),
    (1000, 168),
    (10000, 1229),
    (5000000, 348513),
    (50000000, 3001134),
    (100000000, 5761455),
]

for n, exp in CASES:
    got = primes.count_primes(n)
    if got != exp:
        print(0)
        sys.exit(0)

# Verify CLI execution
out = subprocess.check_output([sys.executable, 'primes.py', '5000000']).decode().strip()
if out != '348513':
    print(0)
    sys.exit(0)

# Benchmark: mix of 5M, 50M, 100M, 200M
t0 = time.perf_counter()
for _ in range(5):
    if primes.count_primes(5000000) != 348513:
        print(0); sys.exit(0)
for _ in range(3):
    if primes.count_primes(50000000) != 3001134:
        print(0); sys.exit(0)
for _ in range(2):
    if primes.count_primes(100000000) != 5761455:
        print(0); sys.exit(0)
dt = time.perf_counter() - t0
print(f"{10.0 / dt:.2f}")
