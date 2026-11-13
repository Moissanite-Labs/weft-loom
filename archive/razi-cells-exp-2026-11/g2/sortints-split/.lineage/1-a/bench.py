import os, random, subprocess, sys, time

DATA = 'data_1m.txt'
SMALL = 'data_200k.txt'
SEED = 12345

def gen(n, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    r = random.Random(SEED)
    with open(path, 'w') as f:
        chunk = []
        for _ in range(n):
            chunk.append(str(r.randint(-2**31, 2**31)))
            if len(chunk) == 10000:
                f.write(' '.join(chunk) + ' ')
                chunk = []
        if chunk:
            f.write(' '.join(chunk))
        f.write('\n')

def run(inp, out):
    with open(inp, 'rb') as fi, open(out, 'wb') as fo:
        t = time.perf_counter()
        p = subprocess.run([sys.executable, 'sortints.py'], stdin=fi, stdout=fo, stderr=subprocess.DEVNULL)
        dt = time.perf_counter() - t
    return p.returncode, dt

def main():
    gen(200000, SMALL)
    gen(1000000, DATA)
    rc, _ = run(SMALL, 'out_small.txt')
    if rc != 0:
        print(0); return
    with open(SMALL) as f:
        ref = sorted(map(int, f.read().split()))
    with open('out_small.txt') as f:
        txt = f.read().split()
    if len(txt) != len(ref):
        print(0); return
    got = [int(x) for x in txt]
    if got != ref:
        print(0); return
    best = None
    for _ in range(3):
        rc, dt = run(DATA, os.devnull)
        if rc != 0:
            print(0); return
        best = dt if best is None else min(best, dt)
    print(1.0 / best)

main()
