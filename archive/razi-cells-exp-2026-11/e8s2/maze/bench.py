import os
import random
import subprocess
import sys
import time
from collections import deque

def gen_maze(N=2000, seed=42):
    rng = random.Random(seed)
    pool_size = 100000
    pool = bytes(ord('.') if rng.random() < 0.72 else ord('#') for _ in range(pool_size))
    rows = [bytearray(b'#' * N)]
    for r in range(1, N - 1):
        offset = rng.randint(0, pool_size - N - 1)
        row = bytearray(pool[offset:offset+N])
        row[0] = ord('#')
        row[N-1] = ord('#')
        if r % 50 == 25:
            if (r // 50) % 2 == 0:
                row[1:N-15] = b'#' * (N - 16)
                row[N-15:N-1] = b'.' * 14
            else:
                row[15:N-1] = b'#' * (N - 16)
                row[1:15] = b'.' * 14
        rows.append(row)
    rows.append(bytearray(b'#' * N))
    # Carve a guaranteed winding backbone so connectivity is 100% certain
    r, c = 1, 1
    for target_r in range(25, N - 1, 50):
        target_c = N - 8 if (target_r // 50) % 2 == 0 else 8
        while c != target_c:
            rows[r][c] = ord('.')
            c += 1 if target_c > c else -1
        while r != target_r + 1:
            rows[r][c] = ord('.')
            r += 1
    while c != N - 2:
        rows[r][c] = ord('.')
        c += 1 if (N - 2) > c else -1
    while r != N - 2:
        rows[r][c] = ord('.')
        r += 1
    rows[1][1] = ord('S')
    rows[N-2][N-2] = ord('E')
    return b'\n'.join(rows) + b'\n'

def ref_solve(data):
    w = data.find(b'\n')
    stride = w + 1
    pad = b'#' * stride
    grid = bytearray(pad + data + pad)
    s = grid.find(b'S')
    e = grid.find(b'E')
    grid[s] = 35
    grid[e] = 46
    q = deque([s])
    dist = 0
    while q:
        dist += 1
        for _ in range(len(q)):
            u = q.popleft()
            for v in (u - 1, u + 1, u - stride, u + stride):
                if grid[v] == 46:
                    if v == e:
                        return dist
                    grid[v] = 35
                    q.append(v)
    return -1

if not os.path.exists('ans.txt'):
    m1 = gen_maze(2000, 42)
    ans1 = ref_solve(m1)
    m2 = gen_maze(2000, 99)
    ans2 = ref_solve(m2)
    with open('maze1.bin', 'wb') as f:
        f.write(m1)
    with open('maze2.bin', 'wb') as f:
        f.write(m2)
    with open('ans.txt', 'w') as f:
        f.write(f"{ans1}\n{ans2}\n")

with open('maze1.bin', 'rb') as f:
    m1 = f.read()
with open('maze2.bin', 'rb') as f:
    m2 = f.read()
with open('ans.txt', 'r') as f:
    ans1, ans2 = [int(x) for x in f.read().split()]

small_cases = [
    (b"S.E\n", 2),
    (b"S#E\n", -1),
    (b"###\n#S#\n#.#\n#E#\n###\n", 2),
    (b"...\n.S.\n...\n", -1),
    (b"S...\n.##.\n..#E\n", 5),
    (b"S..#\n.##.\n..#E\n", -1),
]
for sc, exp in small_cases:
    p = subprocess.run([sys.executable, 'maze.py'], input=sc, capture_output=True)
    if p.returncode != 0 or p.stdout.strip() != str(exp).encode():
        print(0)
        sys.exit(0)

t0 = time.perf_counter()
for m, exp in ((m1, ans1), (m2, ans2)):
    p = subprocess.run([sys.executable, 'maze.py'], input=m, capture_output=True)
    if p.returncode != 0 or p.stdout.strip() != str(exp).encode():
        print(0)
        sys.exit(0)
dt = time.perf_counter() - t0
print(f"{200.0 / dt:.2f}")
