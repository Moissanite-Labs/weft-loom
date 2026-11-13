import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PRIMES = os.path.join(HERE, 'primes.py')
EXPECT = {6: 3, 10: 4, 100: 25, 1000: 168, 100000: 9592,
          1000000: 78498, 5000000: 348513}


def run(n):
    return subprocess.run([sys.executable, PRIMES, str(n)],
                          capture_output=True, text=True)


def main():
    for n, e in EXPECT.items():
        r = run(n)
        try:
            got = int(r.stdout.strip())
        except Exception:
            print(0.0)
            return
        if r.returncode != 0 or got != e:
            print(0.0)
            return
    # heavy, fixed workload: dominated by the real per-invocation cost
    pairs = [(5000000, EXPECT[5000000]), (1000000, EXPECT[1000000])] * 12
    t0 = time.perf_counter()
    for n, e in pairs:
        r = run(n)
        if int(r.stdout.strip()) != e:
            print(0.0)
            return
    elapsed = time.perf_counter() - t0
    print(f"{1.0 / elapsed * 1000.0:.6f}")


if __name__ == '__main__':
    main()
