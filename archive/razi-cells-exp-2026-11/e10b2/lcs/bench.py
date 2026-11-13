import subprocess, sys, time
from lcs import lcs
inp = open('big.txt').read()
exp = open('big.exp').read().strip()
# end-to-end correctness check through the real CLI
out = subprocess.run([sys.executable, 'lcs.py'], input=inp, capture_output=True, text=True).stdout.strip()
if out != exp:
    print(0); sys.exit(0)
a, b = inp.split('\n')[:2]
N = 20
best = None
pc = time.perf_counter
for _ in range(40):  # min over many short batches: robust to load spikes
    t = pc()
    for _ in range(N):
        r = lcs(a, b)
    d = pc() - t
    if best is None or d < best:
        best = d
if str(r) != exp:
    print(0); sys.exit(0)
print(round(N / best, 1))
