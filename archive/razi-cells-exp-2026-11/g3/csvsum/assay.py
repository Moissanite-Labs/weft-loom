import os, subprocess, sys, time

here = os.path.dirname(os.path.abspath(__file__))
prog = os.path.join(here, "csvsum.py")
data = os.path.join(here, "data.csv")
exp = open(os.path.join(here, "expected.txt"), "rb").read()

best = 1e9
for _ in range(2):
    with open(data, "rb") as f:
        t = time.perf_counter()
        p = subprocess.run([sys.executable, prog], stdin=f,
                           stdout=subprocess.PIPE)
        dt = time.perf_counter() - t
    if p.returncode != 0 or p.stdout != exp:
        print(0)
        sys.exit(0)
    if dt < best:
        best = dt
# rows per second (2,000,000 data rows)
print(int(2_000_000 / best))
