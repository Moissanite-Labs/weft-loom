import subprocess, sys, time

EXPECT = {10: 4, 100: 25, 1000: 168, 30: 10, 999983: 78497,
          1000000: 78498, 5000000: 348513, 3: 1, 4: 2}

for n, e in EXPECT.items():
    out = subprocess.run([sys.executable, 'primes.py', str(n)], capture_output=True, text=True)
    if out.returncode != 0 or out.stdout.strip() != str(e):
        print(0)
        sys.exit(0)

REPS = 20
t0 = time.perf_counter()
for _ in range(REPS):
    subprocess.run([sys.executable, 'primes.py', '5000000'], capture_output=True)
t = time.perf_counter() - t0
print(round(1000.0 / (t / REPS), 3))
