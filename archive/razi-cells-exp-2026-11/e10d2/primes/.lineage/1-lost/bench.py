import subprocess, time, sys
# correctness
chk = subprocess.run([sys.executable, "primes.py", "5000000"], capture_output=True, text=True).stdout.strip()
if chk != "348513":
    print(0); sys.exit(0)
chk2 = subprocess.run([sys.executable, "primes.py", "100"], capture_output=True, text=True).stdout.strip()
if chk2 != "25":
    print(0); sys.exit(0)
best = 1e9
for _ in range(3):
    t = time.perf_counter()
    out = subprocess.run([sys.executable, "primes.py", "300000000"], capture_output=True, text=True).stdout.strip()
    dt = time.perf_counter() - t
    if out != "16252325":
        print(0); sys.exit(0)
    best = min(best, dt)
print(round(1000.0 / best, 2))
