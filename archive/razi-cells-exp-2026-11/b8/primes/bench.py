import subprocess
import sys
import time

# 1. Verify CLI interface and edge cases
cases = [
    (0, 0), (1, 0), (2, 0), (3, 1), (4, 2), (5, 2), (6, 3),
    (10, 4), (11, 4), (12, 5), (100, 25), (1000, 168),
    (5000000, 348513),
]
for n, exp in cases:
    out = subprocess.check_output([sys.executable, "primes.py", str(n)], text=True).strip()
    if int(out) != exp:
        print(0)
        sys.exit(0)

# 2. Measure speed by running CLI on 5,000,000 and 50,000,000, plus in-process if available,
# Wait: how is primes.py invoked in reality? "Build primes.py: print the count of primes below int(argv[1]), as fast as possible."
# Let's benchmark actual CLI runs on a mix of N (5_000_000 x 5, 50_000_000 x 3, 100_000_000 x 2)
# OR in-process? If someone runs `python3 primes.py N`, startup + execution both matter!
t0 = time.perf_counter()
for _ in range(4):
    out = subprocess.check_output([sys.executable, "primes.py", "5000000"])
    if int(out) != 348513:
        print(0); sys.exit(0)
for _ in range(3):
    out = subprocess.check_output([sys.executable, "primes.py", "50000000"])
    if int(out) != 3001134:
        print(0); sys.exit(0)
for _ in range(2):
    out = subprocess.check_output([sys.executable, "primes.py", "100000000"])
    if int(out) != 5761455:
        print(0); sys.exit(0)
elapsed = time.perf_counter() - t0
print(f"{100.0 / elapsed:.2f}")
