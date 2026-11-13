import subprocess, sys, time

N = 100_000_000          # workload size
EXPECTED = 5761455       # pi(1e8)

def run_once():
    t0 = time.perf_counter()
    out = subprocess.run([sys.executable, "primes.py", str(N)],
                         capture_output=True, text=True)
    dt = time.perf_counter() - t0
    return out.stdout.strip(), dt

best = None
ok = True
for _ in range(3):
    val, dt = run_once()
    if val != str(EXPECTED):
        ok = False
        break
    if best is None or dt < best:
        best = dt

if not ok or best is None or best <= 0:
    print(0)
else:
    # higher is better: candidates per second
    print(N / best)
