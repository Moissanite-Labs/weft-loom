import subprocess
import sys
import time

CHECKS = [
    (0, 0),
    (1, 0),
    (2, 0),
    (3, 1),
    (4, 2),
    (5, 2),
    (6, 3),
    (7, 3),
    (8, 4),
    (10, 4),
    (11, 4),
    (12, 5),
    (29, 9),
    (30, 10),
    (31, 10),
    (32, 11),
    (100, 25),
    (1000, 168),
    (10000, 1229),
    (100000, 9592),
    (1000000, 78498),
    (5000000, 348513),
]

BENCH_CASES = [
    (5000000, 348513),
    (50000000, 3001134),
    (200000000, 11078937),
    (500000000, 26355867),
]

def main():
    # Verify correctness on edge cases first
    for n, expected in CHECKS:
        res = subprocess.run([sys.executable, "primes.py", str(n)], capture_output=True, text=True)
        if res.returncode != 0:
            print(0)
            return
        try:
            val = int(res.stdout.strip())
        except ValueError:
            print(0)
            return
        if val != expected:
            print(0)
            return

    # Timed workload
    t0 = time.perf_counter()
    for n, expected in BENCH_CASES:
        res = subprocess.run([sys.executable, "primes.py", str(n)], capture_output=True, text=True)
        if res.returncode != 0 or int(res.stdout.strip()) != expected:
            print(0)
            return
    elapsed = time.perf_counter() - t0
    # Score is operations per second (or 1000 / elapsed)
    print(f"{1000.0 / elapsed:.2f}")

if __name__ == "__main__":
    main()
