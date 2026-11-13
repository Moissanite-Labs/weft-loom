import subprocess
import time
import sys

with open("expected.txt", "rb") as f:
    expected = f.read()

# Verify correctness first
res = subprocess.run([sys.executable, "sortints.py"], stdin=open("input.txt", "rb"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if res.returncode != 0 or res.stdout != expected:
    print(0)
    sys.exit(0)

# Run N times to get ~0.5-1.5s total time
N = 5
t0 = time.perf_counter()
for _ in range(N):
    subprocess.run([sys.executable, "sortints.py"], stdin=open("input.txt", "rb"), stdout=subprocess.DEVNULL)
t1 = time.perf_counter()
elapsed = (t1 - t0) / N
# Score = Million ints per second (or 1000 / ms)
print(f"{1000.0 / (elapsed * 1000.0):.4f}")
