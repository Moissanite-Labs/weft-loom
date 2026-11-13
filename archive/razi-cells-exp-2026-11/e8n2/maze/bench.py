import random
import subprocess
import sys
import time
from collections import deque
import maze

def ref_bfs(grid_bytes):
    lines = [line for line in grid_bytes.splitlines() if line]
    if not lines:
        return -1
    H = len(lines)
    W = len(lines[0])
    s = e = None
    for r in range(H):
        for c in range(W):
            ch = lines[r][c]
            if ch == ord('S'):
                s = (r, c)
            elif ch == ord('E'):
                e = (r, c)
    if s is None or e is None:
        return -1
    if s == e:
        return 0
    q = deque([(s[0], s[1], 0)])
    vis = {s}
    while q:
        r, c, d = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in vis:
                ch = lines[nr][nc]
                if (nr, nc) == e:
                    return d + 1
                if ch == ord('.'):
                    vis.add((nr, nc))
                    q.append((nr, nc, d + 1))
    return -1

def test_correctness():
    # 1. Edge cases: no border walls, S at corners, unreachable, 1x2, etc.
    cases = [
        (b"SE\n", 1),
        (b"S.E\n", 2),
        (b"S#E\n", -1),
        (b"S.\n.E\n", 2),
        (b"#S\nE#\n", -1),
        (b".S\nE.\n", 2),
        (b"...\n.S.\n..E\n", 2),
        (b"S..#\n.##.\n....\n#..E\n", 6),
        (b"####\n#S.#\n#.#E\n####\n", 3),
        (b"S\n.\n.\nE\n", 3),
    ]
    for data, expected in cases:
        got = maze.solve(data)
        assert got == expected, f"Failed on {data!r}: got {got}, expected {expected}"
        assert ref_bfs(data) == expected
        # also test CRLF and missing trailing newline
        assert maze.solve(data.rstrip(b"\n")) == expected
        assert maze.solve(data.replace(b"\n", b"\r\n")) == expected

    # 2. Random small and medium grids against reference BFS
    rng = random.Random(12345)
    for idx in range(50):
        H = rng.randint(2, 40)
        W = rng.randint(2, 40)
        wall_p = rng.uniform(0.1, 0.45)
        grid = [bytearray(b'.' if rng.random() > wall_p else b'#' for _ in range(W)) for _ in range(H)]
        sr, sc = rng.randrange(H), rng.randrange(W)
        er, ec = rng.randrange(H), rng.randrange(W)
        while (er, ec) == (sr, sc):
            er, ec = rng.randrange(H), rng.randrange(W)
        grid[sr][sc] = ord('S')
        grid[er][ec] = ord('E')
        raw = b"\n".join(bytes(r) for r in grid) + b"\n"
        exp = ref_bfs(raw)
        got = maze.solve(raw)
        if got != exp:
            print(f"Mismatch on random grid {idx}: got {got}, expected {exp}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    test_correctness()
    with open('maze2000.txt', 'rb') as f:
        data2000 = f.read()
    # Verify 2000x2000 answer (4018)
    ans = maze.solve(data2000)
    if ans != 4018:
        print(0)
        sys.exit(1)
    # Also verify CLI execution on a small maze
    out = subprocess.check_output([sys.executable, 'maze.py'], input=b"S..\n.#.\n..E\n")
    if int(out.strip()) != 4:
        print(0)
        sys.exit(1)

    # Benchmark 2000x2000 maze over enough iterations (~0.5-1.5s)
    iters = 5
    t0 = time.perf_counter()
    for _ in range(iters):
        res = maze.solve(data2000)
        if res != 4018:
            print(0)
            sys.exit(1)
    elapsed = time.perf_counter() - t0
    # Score = mazes solved per second
    print(f"{iters / elapsed:.2f}")
