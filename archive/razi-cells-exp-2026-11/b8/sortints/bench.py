import subprocess
import time
import sys

with open("expected.txt", "rb") as f:
    expected = f.read()

times = []
for i in range(3):
    with open("input.txt", "rb") as fin:
        t0 = time.perf_counter()
        proc = subprocess.run([sys.executable, "sortints.py"], stdin=fin, capture_output=True)
        t1 = time.perf_counter()
    if proc.returncode != 0 or proc.stdout != expected:
        print(0)
        sys.exit(0)
    times.append(t1 - t0)

# Score: 1,000,000 / median_time (ints per second)
times.sort()
print(f"{1000000.0 / times[1]:.1f}")
