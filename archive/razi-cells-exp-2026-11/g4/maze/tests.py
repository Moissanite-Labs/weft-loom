import random, subprocess, sys
from collections import deque

def naive(data):
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    lines = [ln[:-1] if ln.endswith(b'\r') else ln for ln in lines]
    if not lines:
        return -1
    w = max(len(ln) for ln in lines)
    h = len(lines)
    if w == 0:
        return -1
    grid = [ln.ljust(w, b'#') for ln in lines]
    s = e = None
    for y in range(h):
        for x in range(w):
            c = grid[y][x:x+1]
            if c == b'S': s = (x, y)
            elif c == b'E': e = (x, y)
    if s is None or e is None:
        return -1
    dist = {s: 0}
    q = deque([s])
    while q:
        x, y = q.popleft()
        if (x, y) == e:
            return dist[(x, y)]
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < h and grid[ny][nx:nx+1] in (b'.', b'S', b'E') and (nx, ny) not in dist:
                dist[(nx, ny)] = dist[(x, y)] + 1
                q.append((nx, ny))
    return -1

def run_maze(data):
    p = subprocess.run([sys.executable, 'maze.py'], input=data,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        return 'ERR:' + p.stderr.decode()[:200]
    return p.stdout.decode().strip()

cases = []
cases.append(b'S.E\n')
cases.append(b'S#E\n')
cases.append(b'S\nE\n')
cases.append(b'.S.\n.#.\n.E.\n')
cases.append(b'')
cases.append(b'\n')
cases.append(b'S..\n.E.\n...\n')
cases.append(b'#####\n#S..#\n###.#\n#E..#\n#####\n')
cases.append(b'S.E' )  # no trailing newline
cases.append(b'S\r\n.\r\nE\r\n')

rnd = random.Random(12345)
for t in range(240):
    w = rnd.randint(1, 28)
    h = rnd.randint(1, 28)
    dens = rnd.choice([0.0, 0.1, 0.25, 0.4, 0.55, 0.7])
    cells = [['.' if rnd.random() > dens else '#' for _ in range(w)] for _ in range(h)]
    pts = [(x, y) for y in range(h) for x in range(w)]
    sx, sy = rnd.choice(pts)
    ex, ey = rnd.choice(pts)
    cells[sy][sx] = 'S'
    cells[ey][ex] = 'E'
    rows = [''.join(r).encode() for r in cells]
    cases.append(b'\n'.join(rows) + (b'\n' if rnd.random() < 0.5 else b''))

bad = 0
for i, data in enumerate(cases):
    exp = naive(data)
    got = run_maze(data)
    if str(exp) != got:
        bad += 1
        print('MISMATCH case', i, 'exp', exp, 'got', got, 'input:', data[:100])
        if bad > 8:
            break
print('tested', len(cases), 'mismatches', bad)
sys.exit(1 if bad else 0)
