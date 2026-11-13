import os, subprocess, sys, time

DATA = 'test_1m.txt'
REF = 'ref_1m.bin'

def make_data():
    import numpy as np
    rs = np.random.RandomState(1234)
    a = rs.randint(-2**31, 2**31, size=1_000_000, dtype=np.int64)
    with open(DATA, 'w') as f:
        f.write('\n'.join(map(str, a.tolist())))
        f.write('\n')

def make_ref():
    D = open(DATA, 'rb').read()
    vals = sorted(map(int, D.split()))
    out = ('\n'.join(map(str, vals)) + '\n').encode()
    open(REF, 'wb').write(out)
    return out

def main():
    if not os.path.exists(DATA):
        make_data()
    if os.path.exists(REF):
        ref = open(REF, 'rb').read()
    else:
        ref = make_ref()
    best = 1e9
    n = 1_000_000
    for _ in range(3):
        t = time.perf_counter()
        p = subprocess.run([sys.executable, 'sortints.py'], stdin=open(DATA, 'rb'),
                           stdout=subprocess.PIPE)
        dt = time.perf_counter() - t
        if p.returncode != 0:
            print(0.0)
            return
        if p.stdout != ref:
            print(0.0)
            return
        best = min(best, dt)
    print(n / best)

main()
