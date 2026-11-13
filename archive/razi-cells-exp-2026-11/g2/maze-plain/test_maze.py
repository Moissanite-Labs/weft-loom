import random, time
from collections import deque
import maze

def ref_solve(data):
    lines = data.split(b'\n')
    while lines and lines[-1] == b'':
        lines.pop()
    if not lines:
        return -1
    H = len(lines)
    W = max(len(l) for l in lines)
    grid = []
    for l in lines:
        row = l.rstrip(b'\r').decode()
        row = row + '#' * (W - len(row))
        grid.append(list(row))
    s = e = None
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 'S': s = (r, c)
            elif grid[r][c] == 'E': e = (r, c)
    if s is None or e is None:
        return -1
    if s == e:
        return 0
    q = deque([(s[0], s[1], 0)])
    vis = {s}
    while q:
        r, c, d = q.popleft()
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in vis and grid[nr][nc] != '#':
                if (nr, nc) == e:
                    return d + 1
                vis.add((nr, nc))
                q.append((nr, nc, d + 1))
    return -1

def test_small():
    cases = [
        (b'S', -1),
        (b'S. .E', 3),
        (b'S..\n..#\n..E', 4),
        (b'S#E', -1),
        (b'#####\n#S..#\n#.#.#\n#..E#\n#####', 4),
        (b'S\n.\nE', 2),
        (b'S.\n.E', 2),
        (b'S..#\n.#.#\n...E', 5),
        (b'.S.\n.#.\n.E.', 3),
        (b'S.E', 2),
    ]
    for data, want in cases:
        got = maze.solve(data)
        rg = ref_solve(data)
        assert got == want, (data, got, want)
        assert rg == want, (data, rg, want)
    print('small tests OK')

def gen(H, W, seed, density):
    rng = random.Random(seed)
    rows = []
    for r in range(H):
        row = bytearray(b'.' * W)
        for c in range(W):
            if rng.random() < density:
                row[c] = ord('#')
        rows.append(row)
    rows[1][1] = ord('S')
    rows[H-2][W-2] = ord('E')
    return b'\n'.join(bytes(row) for row in rows)

def bench():
    data = gen(2000, 2000, 12345, 0.28)
    t0 = time.perf_counter()
    ans = maze.solve(data)
    dt = time.perf_counter() - t0
    print('bench ans', ans, 'time', dt, 'score', 1.0/dt)
    # correctness spot check on a medium maze vs ref
    d2 = gen(60, 60, 7, 0.25)
    a = maze.solve(d2); b = ref_solve(d2)
    assert a == b, (a, b)
    print('medium agree', a)

if __name__ == '__main__':
    test_small()
    bench()
