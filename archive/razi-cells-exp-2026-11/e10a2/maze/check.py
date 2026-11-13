import subprocess, sys
from gen import gen
bad = 0
cases = []
for seed in range(60):
    n = 1 + seed % 13; m = 1 + (seed * 7) % 17
    if n * m < 2: m = 2
    cases.append(gen(n, m, seed, 0.2 + 0.03 * (seed % 8)))
cases += ["S.E\n", "S#E\n", "E..\n.#.\n..S\n", "S\n#\nE\n", "..S..\n.###.\n..E..\n"]
for t in cases:
    a = subprocess.run([sys.executable, 'maze.py'], input=t.encode(), capture_output=True).stdout.strip()
    b = subprocess.run([sys.executable, 'ref.py'], input=t.encode(), capture_output=True).stdout.strip()
    if a != b:
        bad += 1; print('MISMATCH', repr(t), a, b)
print('cases', len(cases), 'bad', bad)
