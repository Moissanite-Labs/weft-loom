import subprocess, sys, time

# (n, expected count of primes below n)
CHECKS = [(0, 0), (2, 0), (3, 1), (100, 25), (1000, 168), (5000000, 348513)]
HEAVY = [(100000000, 5761455), (200000000, 11078937), (300000000, 16252325)]


def run(n):
    out = subprocess.run([sys.executable, "primes.py", str(n)],
                         capture_output=True, text=True, timeout=25).stdout.strip()
    return out


try:
    for n, want in CHECKS:
        if run(n) != str(want):
            print(0)
            sys.exit(0)
    t0 = time.perf_counter()
    for n, want in HEAVY:
        if run(n) != str(want):
            print(0)
            sys.exit(0)
    dt = time.perf_counter() - t0
    print(round(100.0 / dt, 3))
except Exception:
    print(0)
