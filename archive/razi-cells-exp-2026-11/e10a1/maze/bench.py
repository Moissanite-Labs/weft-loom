import subprocess, time, sys
exp = {'big.txt': open('big.expected').read().strip(), 'blocked.txt': '-1', 's.txt': '24', 't.txt': '-1'}
for f in ('blocked.txt', 's.txt', 't.txt'):
    out = subprocess.run([sys.executable, 'maze.py'], stdin=open(f, 'rb'), capture_output=True).stdout.decode().strip()
    if out != exp[f]:
        print(0); sys.exit(0)
best = 1e9
for _ in range(3):
    t = time.perf_counter()
    out = subprocess.run([sys.executable, 'maze.py'], stdin=open('big.txt', 'rb'), capture_output=True).stdout.decode().strip()
    dt = time.perf_counter() - t
    if out != exp['big.txt']:
        print(0); sys.exit(0)
    best = min(best, dt)
print(round(1.0 / best, 4))
