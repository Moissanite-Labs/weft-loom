import subprocess, time, sys, hashlib

with open('expected.txt', 'rb') as f:
    expected_bytes = f.read()

# Verify correctness first
p = subprocess.run([sys.executable, 'sortints.py'], stdin=open('input.txt', 'rb'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if p.returncode != 0 or p.stdout != expected_bytes:
    print(0)
    sys.exit(0)

# Time 3 runs and take median
times = []
for _ in range(3):
    with open('input.txt', 'rb') as fin, open('/dev/null', 'wb') as fout:
        t0 = time.perf_counter()
        subprocess.run([sys.executable, 'sortints.py'], stdin=fin, stdout=fout, check=True)
        t1 = time.perf_counter()
        times.append(t1 - t0)

times.sort()
median_time = times[1]
# Score = million ints per second (or 1000 / median_time)
print(f"{1000.0 / median_time:.2f}")
