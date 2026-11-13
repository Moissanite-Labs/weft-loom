import random, subprocess, sys, time
from collections import deque

PY = sys.executable


def gen(h, w, seed, wall_p=0.30):
    rnd = random.Random(seed)
    raw = rnd.randbytes(h * w)
    thresh = int(wall_p * 256)
    tbl = bytes(35 if b < thresh else 46 for b in range(256))
    data = bytearray(raw.translate(tbl))
    data[0] = 83
    data[-1] = 69
    return b'\n'.join(bytes(data[y * w:(y + 1) * w]) for y in range(h))


def run(grid_bytes):
    p = subprocess.run([PY, 'maze2.py'], input=grid_bytes, capture_output=True, timeout=120)
    if p.returncode != 0:
        return 'ERR'
    return p.stdout.decode().strip()


def ref(grid_bytes):
    lines = [l for l in grid_bytes.split(b'\n') if l]
    if not lines:
        return '-1'
    h = len(lines); w = len(lines[0])
    s = e = None
    for y, row in enumerate(lines):
        i = row.find(b'S')
        if i >= 0: s = (y, i)
        i = row.find(b'E')
        if i >= 0: e = (y, i)
    if s is None or e is None:
        return '-1'
    if s == e:
        return '0'
    dist = [[-1] * w for _ in range(h)]
    dist[s[0]][s[1]] = 0
    dq = deque([s])
    while dq:
        y, x = dq.popleft()
        d = dist[y][x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and dist[ny][nx] < 0 and lines[ny][nx] in b'.SE':
                if (ny, nx) == e:
                    return str(d + 1)
                dist[ny][nx] = d + 1
                dq.append((ny, nx))
    return '-1'


def correctness():
    cases = [
        b'S.E',
        b'S#E',
        b'S\n.\nE',
        b'###\n#S#\n#.#\n#E#\n###',
        b'S..\n.#.\n..E',
        b'S#\n#E',
        b'S..\n###\n..E',
        b'S',
        b'E',
        b'SE',
    ]
    for c in cases:
        got = run(c)
        exp = ref(c)
        if got != exp:
            print('FAIL', c, got, exp, file=sys.stderr)
            return False
    rnd = random.Random(7)
    for _ in range(30):
        h = rnd.randint(1, 12); w = rnd.randint(1, 12)
        lines = [bytearray(35 if rnd.random() < 0.35 else 46 for _ in range(w)) for _ in range(h)]
        sy, sx = rnd.randrange(h), rnd.randrange(w)
        ey, ex = rnd.randrange(h), rnd.randrange(w)
        lines[sy][sx] = 83
        lines[ey][ex] = 69
        g = b'\n'.join(bytes(r) for r in lines)
        got = run(g); exp = ref(g)
        if got != exp:
            print('FAIL', g, got, exp, file=sys.stderr)
            return False
    return True


def main():
    if not correctness():
        print(0)
        return
    g = gen(2000, 2000, 12345)
    t0 = time.perf_counter()
    out = run(g)
    t1 = time.perf_counter()
    if out != '-1' and not out.isdigit():
        print(0)
        return
    if out != '-1' and int(out) < 1:
        print(0)
        return
    print(1.0 / (t1 - t0))


main()
