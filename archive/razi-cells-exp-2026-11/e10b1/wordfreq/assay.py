import subprocess, sys, time

# Fitness = 1 / best-of-9 wall time of wf.py on big.txt (20MB); 0 if output is wrong.
# One warm-up run first (not timed) so file cache / interpreter startup are warm.
exp = open("expected.txt", "rb").read()

def run():
    with open("big.txt", "rb") as f:
        t = time.perf_counter()
        p = subprocess.run([sys.executable, "wf.py"], stdin=f, stdout=subprocess.PIPE)
        dt = time.perf_counter() - t
    return p, dt

p, _ = run()
if p.returncode != 0 or p.stdout != exp:
    print(0)
    sys.exit(0)
best = None
for _ in range(9):
    p, dt = run()
    if p.returncode != 0 or p.stdout != exp:
        print(0)
        sys.exit(0)
    best = dt if best is None else min(best, dt)
print("%.4f" % (1.0 / best))
