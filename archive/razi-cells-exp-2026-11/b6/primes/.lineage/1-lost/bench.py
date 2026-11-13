import subprocess, sys, time
cases = [(5000000,348513), (10000000,664579), (20000000,1270607), (50000000,3001134)]
t = time.perf_counter()
for _ in range(3):
    for n, expected in cases:
        p = subprocess.run([sys.executable, 'primes.py', str(n)], capture_output=True)
        if p.returncode or p.stdout.strip() != str(expected).encode():
            print(0)
            sys.exit(0)
print(1 / (time.perf_counter()-t))
