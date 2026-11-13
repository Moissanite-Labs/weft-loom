import os, subprocess, sys, time
import numpy as np

N = 1_000_000
if not os.path.exists('data.txt') or os.path.getsize('data.txt') < 1000:
    rng = np.random.default_rng(12345)
    a = rng.integers(-10**9, 10**9 + 1, size=N)
    with open('data.txt', 'w') as f:
        f.write('\n'.join(map(str, a)) + '\n')
data = open('data.txt', 'rb').read()
vals = np.fromstring(data, dtype=np.int64, sep=' ')
assert len(vals) == N, len(vals)
expected = ('\n'.join(map(str, np.sort(vals).tolist())) + '\n').encode()

def once():
    with open('data.txt', 'rb') as fi, open('.tmp/out.txt', 'wb') as fo:
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, 'sortints.py'], stdin=fi, stdout=fo,
                           stderr=subprocess.DEVNULL)
        t1 = time.perf_counter()
    if r.returncode != 0:
        return None
    if open('.tmp/out.txt', 'rb').read() != expected:
        return None
    return t1 - t0

times = []
for _ in range(3):
    t = once()
    if t is None:
        sys.stdout.write("0\n")
        sys.exit(0)
    times.append(t)
best = min(times)
sys.stdout.write("%.1f\n" % (N / best))
