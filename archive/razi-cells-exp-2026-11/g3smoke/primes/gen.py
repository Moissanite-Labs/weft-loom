import subprocess, sys, time

TEMPLATE = '''import sys
import numpy as np

SEG = %d

def count_primes(n):
    if n < 3:
        return 0
    half = (n + 1) // 2
    lim = int(n ** 0.5)
    while (lim + 1) * (lim + 1) <= n:
        lim += 1
    bh = (lim + 1) // 2
    b = np.ones(bh, dtype=bool)
    b[0] = False
    i = 1
    while (2 * i + 1) * (2 * i + 1) <= lim:
        if b[i]:
            p = 2 * i + 1
            b[(p * p) // 2::p] = False
        i += 1
    primes = (2 * np.nonzero(b)[0] + 1).tolist()
    if SEG <= 0:
        seg = np.ones(half, dtype=bool)
        seg[0] = False
        for p in primes:
            seg[p * p // 2::p] = False
        return 1 + int(np.count_nonzero(seg))
    total = 1
    for lo in range(0, half, SEG):
        hi = lo + SEG
        if hi > half:
            hi = half
        seg = np.ones(hi - lo, dtype=bool)
        if lo == 0:
            seg[0] = False
        for p in primes:
            if p * p // 2 >= hi:
                break
            start = p * p // 2
            if start < lo:
                v = 2 * lo + 1
                k = (v + p - 1) // p
                if k %% 2 == 0:
                    k += 1
                start = (k * p) // 2
            if start < hi:
                seg[start - lo::p] = False
        total += int(np.count_nonzero(seg))
    return total

print(count_primes(int(sys.argv[1])))
'''

cands = [0, 1 << 20, 1 << 21, 1 << 22, 1 << 23, 1 << 24]
N = 100_000_000
EXP = "5761455"
results = []
for seg in cands:
    fn = "cand_%d.py" % seg
    open(fn, "w").write(TEMPLATE % seg)
    best = None
    ok = True
    for _ in range(3):
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, fn, str(N)], capture_output=True, text=True)
        dt = time.perf_counter() - t0
        if r.stdout.strip() != EXP:
            ok = False
            print("seg", seg, "WRONG", r.stdout.strip()[:60], r.stderr.strip()[:200])
            break
        best = dt if best is None or dt < best else best
    if ok:
        results.append((best, seg))
        print("seg %9d  best %.4fs  rate %.3e" % (seg, best, N / best))
results.sort()
best_dt, best_seg = results[0]
print("WINNER seg", best_seg, "%.4fs" % best_dt)
open("primes.py", "w").write(TEMPLATE % best_seg)
for argv in ["0", "1", "2", "3", "5", "100", "5000000", "100000000"]:
    r = subprocess.run([sys.executable, "primes.py", argv], capture_output=True, text=True)
    print(argv, "->", r.stdout.strip(), r.stderr.strip()[:100])
