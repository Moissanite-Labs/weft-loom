import subprocess, time, sys
exp = open('expected.txt','rb').read()
times = []
for _ in range(9):
    t = time.perf_counter()
    with open('data.txt','rb') as f:
        r = subprocess.run([sys.executable, 'sortints.py'], stdin=f, stdout=subprocess.PIPE)
    dt = time.perf_counter() - t
    if r.returncode != 0 or r.stdout != exp:
        print(0); sys.exit(0)
    times.append(dt)
print(round(1.0/min(times), 4))
