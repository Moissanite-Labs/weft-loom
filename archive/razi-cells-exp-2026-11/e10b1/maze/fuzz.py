import sys, random, importlib
from collections import deque
m = importlib.import_module(sys.argv[1])
def ref(text):
    g = [r for r in text.split('\n') if r]
    for i, r in enumerate(g):
        if 'S' in r: s = (i, r.index('S'))
        if 'E' in r: e = (i, r.index('E'))
    d = {s: 0}; q = deque([s])
    while q:
        c = q.popleft()
        if c == e: return d[c]
        for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
            a, b = c[0]+di, c[1]+dj
            if 0 <= a < len(g) and 0 <= b < len(g[a]) and g[a][b] != '#' and (a, b) not in d:
                d[(a, b)] = d[c]+1; q.append((a, b))
    return -1
impls = [k for k in ('ext', 'ct') if m._fast(k) is not None] + ['py', None]
print('tiers available:', impls)
r = random.Random(7); bad = 0; cnt = 0; unreach = 0
for it in range(1500):
    n = r.randint(1, 14); w = r.randint(1, 14)
    if n * w < 2: continue
    p = r.choice([0.0, 0.15, 0.3, 0.4, 0.5])
    cells = ['#' if r.random() < p else '.' for _ in range(n*w)]
    a, b = r.sample(range(n*w), 2); cells[a] = 'S'; cells[b] = 'E'
    rows = [''.join(cells[i*w:(i+1)*w]) for i in range(n)]
    mode = it % 4
    if mode == 1: rows = [x.rstrip('#') or '#' for x in rows]
    text = '\n'.join(rows) + ('' if mode == 2 else '\n')
    want = ref(text); unreach += want < 0
    data = text.encode()
    if mode == 3: data = data.replace(b'\n', b'\r\n')
    for k in impls:
        got = m.solve(data, k); cnt += 1
        if got != want:
            bad += 1
            if bad < 4: print('MISMATCH', k, mode, got, want, repr(text))
print('checks', cnt, 'unreachable cases', unreach, 'bad', bad)
sys.exit(1 if bad else 0)
