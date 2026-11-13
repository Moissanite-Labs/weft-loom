import subprocess, time, sys
# Score = 1 / (fastest of 3 runs, seconds). 0 if any run's output differs from expected.txt.
exp = open('expected.txt', 'rb').read()
best = None
ok = True
for _ in range(3):
    t = time.perf_counter()
    with open('data.txt', 'rb') as f:
        out = subprocess.run([sys.executable, 'sortints.py'], stdin=f, stdout=subprocess.PIPE).stdout
    dt = time.perf_counter() - t
    if out != exp:
        ok = False
    if best is None or dt < best:
        best = dt
print(round(1.0 / best, 4) if ok else 0)
