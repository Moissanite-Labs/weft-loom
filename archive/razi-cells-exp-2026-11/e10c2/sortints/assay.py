import subprocess, time, sys, filecmp
best = 1e9
for i in range(3):
    with open('data.txt','rb') as fi, open('out.txt','wb') as fo:
        t = time.perf_counter()
        r = subprocess.run([sys.executable, 'sortints.py'], stdin=fi, stdout=fo)
        t = time.perf_counter() - t
    if r.returncode != 0 or not filecmp.cmp('out.txt', 'expected.txt', shallow=False):
        print(0); sys.exit(0)
    best = min(best, t)
print(1000 / best)
