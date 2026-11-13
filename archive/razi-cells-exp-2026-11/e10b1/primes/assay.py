import subprocess, sys, time

# (n, expected count of primes below n)
CHECKS = [(0, 0), (1, 0), (2, 0), (3, 1), (4, 2), (5, 2), (10, 4), (100, 25),
          (122, 30), (1000, 168), (5000000, 348513)]
TIMED = [(5000000, 348513), (100000000, 5761455), (100000000, 5761455),
         (100000000, 5761455), (30000000, 1857859)]


def run(n):
    try:
        out = subprocess.run([sys.executable, "primes.py", str(n)],
                             capture_output=True, text=True, timeout=25)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def main():
    for n, exp in CHECKS:
        if run(n) != str(exp):
            print(0)
            return
    t0 = time.perf_counter()
    for n, exp in TIMED:
        if run(n) != str(exp):
            print(0)
            return
    dt = time.perf_counter() - t0
    print(round(100.0 / dt, 2))


main()
