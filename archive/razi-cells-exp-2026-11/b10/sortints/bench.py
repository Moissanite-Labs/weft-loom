import subprocess, time, sys

with open('expected_1m.txt', 'rb') as f:
    expected = f.read()

t0 = time.perf_counter()
res = subprocess.run([sys.executable, 'sortints.py'], stdin=open('input_1m.txt', 'rb'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
t1 = time.perf_counter()

if res.returncode != 0 or res.stdout != expected:
    print(0)
    sys.exit(0)

# Score is million ints per second (1 / elapsed_seconds * 1000 for scaling)
elapsed = t1 - t0
print(f"{1000.0 / elapsed:.2f}")
