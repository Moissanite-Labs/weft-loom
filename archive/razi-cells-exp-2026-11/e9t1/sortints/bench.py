import subprocess
import time
import sys

with open("expected.txt", "rb") as f:
    expected = f.read()

# Run 2 iterations inside one benchmark run so total runtime is ~0.3-1.5s
t0 = time.perf_counter()
for _ in range(2):
    with open("input.txt", "rb") as fin:
        p = subprocess.run([sys.executable, "sortints.py"], stdin=fin, capture_output=True)
    if p.returncode != 0 or p.stdout != expected:
        print(0)
        sys.exit(0)
t1 = time.perf_counter()

# Score: millions of ints sorted per second (2M ints / elapsed)
elapsed = t1 - t0
print(f"{2.0 / elapsed:.4f}")
