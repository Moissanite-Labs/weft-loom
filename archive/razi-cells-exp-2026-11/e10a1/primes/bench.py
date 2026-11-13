"""Assay for primes.py: prints a speed score (higher is better), 0 if any output is wrong.

Correctness is checked against an independent trial-division reference for small
and awkward n (edges, squares of primes, primes themselves) and against known
values of pi(n) for large n. Only then is the timed workload run.
The timed workload is repeated several times and the best (minimum) time is
used, which makes the score stable against one-off scheduling hiccups.
"""
import subprocess
import sys
import time


def ref(n):
    c = 0
    for k in range(2, n):
        d = 2
        ok = True
        while d * d <= k:
            if k % d == 0:
                ok = False
                break
            d += 1
        c += ok
    return c


def run(n):
    r = subprocess.run([sys.executable, "primes.py", str(n)],
                       capture_output=True, text=True, timeout=25)
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def main():
    small = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 25, 26, 49, 50,
             121, 122, 168, 169, 170, 997, 998, 1000, 7919, 7920, 10007]
    known = {1000000: 78498, 5000000: 348513, 10000000: 664579,
             50000000: 3001134}
    for n in small:
        if run(n) != str(ref(n)):
            print(0)
            return
    for n, c in known.items():
        if run(n) != str(c):
            print(0)
            return

    # timed workload: the stated target size, repeated, plus larger sizes
    work = [5000000] * 8 + [10000000] * 2 + [50000000]
    best = None
    for _ in range(7):
        t0 = time.perf_counter()
        for n in work:
            if run(n) != str(known[n]):
                print(0)
                return
        dt = time.perf_counter() - t0
        if best is None or dt < best:
            best = dt
    print(round(100.0 / best, 3))


if __name__ == "__main__":
    main()
