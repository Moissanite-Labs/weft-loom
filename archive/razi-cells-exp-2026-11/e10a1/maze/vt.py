import random, subprocess, sys
r = random.Random(7); bad = 0; N = 150
for t in range(N):
    n = r.randint(1, 14); m = r.randint(1, 14)
    if n * m < 2: m = 2
    p = r.choice([0.0, 0.2, 0.35, 0.5])
    g = [['#' if r.random() < p else '.' for _ in range(m)] for _ in range(n)]
    cells = [(i, j) for i in range(n) for j in range(m)]
    s, e = r.sample(cells, 2)
    if t % 5 == 0 and n > 1: e = (r.choice([i for i in range(n) if i != s[0]]), s[1])  # same column
    if t % 7 == 0 and m > 1: e = (s[0], r.choice([j for j in range(m) if j != s[1]]))  # same row
    g[s[0]][s[1]] = 'S'; g[e[0]][e[1]] = 'E'
    txt = '\n'.join(''.join(x) for x in g) + ('\n' if t % 2 else '')
    a = subprocess.run([sys.executable, 'maze.py'], input=txt.encode(), capture_output=True).stdout.decode().strip()
    b = subprocess.run([sys.executable, 'ref.py'], input=txt.encode(), capture_output=True).stdout.decode().strip()
    if a != b:
        bad += 1
        if bad < 4: print('MISMATCH', a, b); print(txt)
print('tested', N, 'bad', bad)
