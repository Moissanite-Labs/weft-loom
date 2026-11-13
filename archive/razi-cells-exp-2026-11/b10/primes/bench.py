import subprocess
import sys
import time

# 1. Verify CLI behavior as required by NEED
out = subprocess.check_output([sys.executable, 'primes.py', '5000000']).strip()
if out != b'348513':
    print(0)
    sys.exit(0)

import primes

# find entry point function
fn = getattr(primes, 'count_primes', None)
if fn is None:
    print(0)
    sys.exit(0)

# 2. Verify correctness across edge cases and larger values
TESTS = [
    (0, 0), (1, 0), (2, 0), (3, 1), (4, 2), (5, 2),
    (6, 3), (7, 3), (8, 4), (9, 4), (10, 4), (11, 4),
    (12, 5), (13, 5), (14, 6), (29, 9), (30, 10), (31, 10), (32, 11),
    (100, 25), (1000, 168), (10000, 1229), (100000, 9592),
    (999983, 78497), (999984, 78498),
    (5000000, 348513),
    (50000000, 3001134),
]

for n, expected in TESTS:
    got = fn(n)
    if got != expected:
        print(0)
        sys.exit(0)

# 3. Benchmark workload (~0.4s baseline)
t0 = time.perf_counter()
for _ in range(40):
    if fn(5000000) != 348513:
        print(0)
        sys.exit(0)
for _ in range(4):
    if fn(50000000) != 3001134:
        print(0)
        sys.exit(0)
dt = time.perf_counter() - t0

print(f"{100.0 / dt:.2f}")
