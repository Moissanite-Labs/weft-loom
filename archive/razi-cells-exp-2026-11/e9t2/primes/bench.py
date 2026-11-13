import subprocess
import sys
import time

CASES = [
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
    (100, 25),
    (1000, 168),
    (100000, 9592),
    (5000000, 348513),
    (50000000, 3001134),
    (200000000, 11078937),
]

def main():
    # 1. Verify CLI correctness on key cases including 5000000
    for n, exp in [(0, 0), (2, 0), (3, 1), (5, 2), (5000000, 348513)]:
        out = subprocess.check_output([sys.executable, "primes.py", str(n)], text=True).strip()
        if int(out) != exp:
            print(0)
            return

    # 2. Benchmark CLI + in-process speed across workloads so startup doesn't mask algorithmic gains
    import primes
    for n, exp in CASES:
        if primes.count_primes(n) != exp:
            print(0)
            return

    t0 = time.perf_counter()
    # Run in-process workloads (5M x 10, 50M x 3, 200M x 1)
    for _ in range(10):
        if primes.count_primes(5000000) != 348513:
            print(0)
            return
    for _ in range(3):
        if primes.count_primes(50000000) != 3001134:
            print(0)
            return
    if primes.count_primes(200000000) != 11078937:
        print(0)
        return
    # Also include 2 CLI runs of 5000000 in timing so slow-import penalties are caught
    for _ in range(2):
        out = subprocess.check_output([sys.executable, "primes.py", "5000000"], text=True).strip()
        if int(out) != 348513:
            print(0)
            return
    dt = time.perf_counter() - t0
    print(f"{1000.0 / dt:.2f}")

if __name__ == "__main__":
    main()
