import subprocess, sys, time
EXP = {}
for ln in open("expected.txt"):
    f, v = ln.split(); EXP[f] = v
# small-case correctness vs reference
out = subprocess.run([sys.executable, "check.py"], capture_output=True, text=True).stdout
if "bad 0 " not in out:
    print(0); sys.exit(0)
best = 0.0
tot = 0.0
for f, v in EXP.items():
    with open(f, "rb") as fh:
        t = time.perf_counter()
        r = subprocess.run([sys.executable, "maze.py"], stdin=fh, capture_output=True, text=True)
        tot += time.perf_counter() - t
    if r.stdout.strip() != v:
        print(0); sys.exit(0)
print(round(10.0 / tot, 3))
