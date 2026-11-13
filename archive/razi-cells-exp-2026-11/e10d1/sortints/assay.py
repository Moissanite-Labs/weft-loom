import subprocess, time, sys, os
d = os.path.dirname(os.path.abspath(__file__))
best = None
for _ in range(3):
    t = time.perf_counter()
    with open(os.path.join(d,'data.txt'),'rb') as fi, open(os.path.join(d,'out.txt'),'wb') as fo:
        r = subprocess.run([sys.executable, os.path.join(d,'sortints.py')], stdin=fi, stdout=fo)
    e = time.perf_counter() - t
    if r.returncode != 0:
        print(0); sys.exit(0)
    best = e if best is None or e < best else best
if open(os.path.join(d,'out.txt'),'rb').read() != open(os.path.join(d,'expected.txt'),'rb').read():
    print(0); sys.exit(0)
print(round(1000.0 / best, 2))
