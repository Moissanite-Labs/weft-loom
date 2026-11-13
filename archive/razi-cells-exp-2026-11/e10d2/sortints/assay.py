import subprocess, time, sys, os
t = time.perf_counter()
with open('in.txt', 'rb') as f, open('out.txt', 'wb') as o:
    r = subprocess.run([sys.executable, 'sortints.py'], stdin=f, stdout=o)
dt = time.perf_counter() - t
if r.returncode != 0:
    print(0); sys.exit(0)
if open('out.txt', 'rb').read() != open('expected.txt', 'rb').read():
    print(0); sys.exit(0)
print(round(1000.0 / dt, 2))
