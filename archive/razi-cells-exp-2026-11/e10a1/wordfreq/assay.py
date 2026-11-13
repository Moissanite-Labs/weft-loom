import subprocess, time, sys
exp = open("expected.txt").read()
best = None
for _ in range(3):
    with open("text.txt", "rb") as f:
        t = time.perf_counter()
        out = subprocess.run([sys.executable, "wf.py"], stdin=f, capture_output=True, text=True)
        dt = time.perf_counter() - t
    if out.returncode != 0 or out.stdout != exp:
        print(0)
        sys.exit(0)
    best = dt if best is None else min(best, dt)
print(round(1.0 / best, 4))
