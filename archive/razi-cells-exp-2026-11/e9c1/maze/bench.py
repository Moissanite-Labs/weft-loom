import random, time, subprocess, sys, os, json
from collections import deque

def ref_solve(data_bytes):
    grid = [list(line) for line in data_bytes.decode().splitlines() if line]
    if not grid: return -1
    h = len(grid)
    w = len(grid[0])
    s = e = None
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 'S': s = (r, c)
            elif grid[r][c] == 'E': e = (r, c)
    if not s or not e: return -1
    if s == e: return 0
    q = deque([(s[0], s[1], 0)])
    grid[s[0]][s[1]] = '#'
    while q:
        r, c, d = q.popleft()
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != '#':
                if (nr, nc) == e:
                    return d + 1
                grid[nr][nc] = '#'
                q.append((nr, nc, d + 1))
    return -1

def make_maze(n, seed, density=0.22, block_end=False):
    rng = random.Random(seed)
    row_bytes = bytearray(b'.#'[rng.random() < density] for _ in range(n * n))
    grid = [row_bytes[i*n:(i+1)*n] for i in range(n)]
    for r in range(200, n - 200, 200):
        if (r // 200) % 2 == 1:
            for c in range(0, n - 200):
                grid[r][c] = 35
        else:
            for c in range(200, n):
                grid[r][c] = 35
    grid[0][0] = ord('S')
    grid[0][1] = ord('.')
    grid[1][0] = ord('.')
    grid[n-1][n-1] = ord('E')
    if block_end:
        grid[n-1][n-2] = ord('#')
        grid[n-2][n-1] = ord('#')
    else:
        grid[n-1][n-2] = ord('.')
        grid[n-2][n-1] = ord('.')
    return b'\n'.join(grid) + b'\n'

def setup():
    if os.path.exists('test_meta.json'):
        return
    m1 = make_maze(2000, 12345, 0.20, False)
    m2 = make_maze(2000, 67890, 0.22, True)
    with open('m1.txt', 'wb') as f: f.write(m1)
    with open('m2.txt', 'wb') as f: f.write(m2)
    ans1 = ref_solve(m1)
    ans2 = ref_solve(m2)
    # Small edge cases
    smalls = [
        b"S.E\n",
        b"S#E\n",
        b"S\n.\nE\n",
        b"...\n.S.\n..E\n",
        b"#S#\n#.#\n#E#\n",
        b"E.S\n... \n".replace(b" ", b""),
    ]
    small_ans = [ref_solve(s) for s in smalls]
    with open('test_meta.json', 'w') as f:
        json.dump({'ans1': ans1, 'ans2': ans2, 'smalls': [s.decode() for s in smalls], 'small_ans': small_ans}, f)
    print("Setup done:", ans1, ans2, small_ans, file=sys.stderr)

def run_bench():
    setup()
    with open('test_meta.json') as f:
        meta = json.load(f)
    with open('m1.txt', 'rb') as f: m1 = f.read()
    with open('m2.txt', 'rb') as f: m2 = f.read()

    # Check small edge cases first (1 subprocess call or individual)
    for s_str, expected in zip(meta['smalls'], meta['small_ans']):
        p = subprocess.run([sys.executable, 'maze.py'], input=s_str.encode(), capture_output=True)
        if p.returncode != 0 or p.stdout.decode().strip() != str(expected):
            print(0)
            return

    # Timed benchmark on 2000x2000 mazes
    t0 = time.perf_counter()
    for m, expected in [(m1, meta['ans1']), (m2, meta['ans2'])]:
        p = subprocess.run([sys.executable, 'maze.py'], input=m, capture_output=True)
        if p.returncode != 0 or p.stdout.decode().strip() != str(expected):
            print(0)
            return
    dt = time.perf_counter() - t0
    # Score: mazes per second * 100
    print(f"{200.0 / dt:.2f}")

if __name__ == '__main__':
    run_bench()
