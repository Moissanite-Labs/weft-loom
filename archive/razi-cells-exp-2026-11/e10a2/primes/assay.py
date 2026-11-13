import subprocess, sys, time

# Known prime counts below n (pi(n-1)); any wrong answer -> score 0.
CHECKS = [
    (0, 0), (1, 0), (2, 0), (3, 1), (4, 2), (5, 2), (10, 4), (100, 25),
    (121, 30), (122, 30), (1000, 168), (5000000, 348513),
]
HEAVY = (100000000, 5761455)


def run(n):
    r = subprocess.run([sys.executable, "primes.py", str(n)],
                       capture_output=True, text=True, timeout=25)
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def main():
    for n, want in CHECKS:
        if run(n) != str(want):
            print(0)
            return
    best = None
    for _ in range(3):
        t = time.perf_counter()
        out = run(HEAVY[0])
        dt = time.perf_counter() - t
        if out != str(HEAVY[1]):
            print(0)
            return
        best = dt if best is None else min(best, dt)
    # score: heavy runs per second (higher is better)
    print(round(1.0 / best, 4))


main()
