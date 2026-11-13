import subprocess, sys, time
# expected answers are filled in from ref.py (independent BFS), see expected.txt
exp = {}
for line in open('expected.txt'):
    f, v = line.split()
    exp[f] = v
small = [("S.E\n", "2"), ("S#E\n", "-1"), ("E..\n.#.\n..S\n", "4"), ("S\n#\nE\n", "-1")]
for t, v in small:
    o = subprocess.run([sys.executable, 'maze.py'], input=t.encode(), capture_output=True).stdout.decode().strip()
    if o != v:
        print(0); sys.exit(0)
t0 = time.perf_counter()
for f, v in exp.items():
    with open(f, 'rb') as fh:
        o = subprocess.run([sys.executable, 'maze.py'], stdin=fh, capture_output=True).stdout.decode().strip()
    if o != v:
        print(0); sys.exit(0)
dt = time.perf_counter() - t0
print(round(100.0 / dt, 3))
