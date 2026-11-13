import subprocess, sys, random
from gen import gen
tgt = sys.argv[1]
bad = 0
cases = []
for seed in range(60):
    n = 1 + seed % 13; m = 1 + (seed * 7) % 17
    if n * m < 2: m = 2
    cases.append(gen(n, m, seed, 0.2 + 0.03 * (seed % 8)))
r = random.Random(7)
for k in range(140):
    n = r.randint(1, 14); m = r.randint(1, 14)
    if n * m < 2: m = 2
    p = r.choice([0, 0.1, 0.25, 0.35, 0.45])
    g = [['#' if r.random() < p else '.' for _ in range(m)] for _ in range(n)]
    a, b = r.sample(range(n * m), 2)
    g[a // m][a % m] = 'S'; g[b // m][b % m] = 'E'
    cases.append('\n'.join(''.join(x) for x in g) + '\n')
# serpentine
rows = []
for i in range(15):
    if i % 2 == 0: rows.append('.' * 15)
    else: rows.append(('#' * 14 + '.') if (i // 2) % 2 == 0 else ('.' + '#' * 14))
rows[0] = 'S' + rows[0][1:]; rows[14] = rows[14][:7] + 'E' + rows[14][8:]
cases.append('\n'.join(rows) + '\n')
cases += ["S.E\n", "S#E\n", "E..\n.#.\n..S\n", "S\n#\nE\n", "..S..\n.###.\n..E..\n", "SE\n", "E\nS\n", "S..\n", "", "...\n.E.\n"]
for t in cases:
    a = subprocess.run([sys.executable, tgt], input=t.encode(), capture_output=True).stdout.strip()
    if 'S' in t and 'E' in t:
        b = subprocess.run([sys.executable, 'ref.py'], input=t.encode(), capture_output=True).stdout.strip()
    else:
        b = b'-1'
    if a != b:
        bad += 1; print('MISMATCH', repr(t), a, b)
print(tgt, 'cases', len(cases), 'bad', bad)
