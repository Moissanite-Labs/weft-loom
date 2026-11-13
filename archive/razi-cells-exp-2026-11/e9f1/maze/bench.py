import os
import random
import subprocess
import sys
import time
from collections import deque

def solve_ref(data_bytes):
    lines = [l for l in data_bytes.splitlines() if l]
    if not lines:
        return -1
    H = len(lines)
    W = len(lines[0])
    W2 = W + 2
    grid = bytearray(b'#' * (W2 * (H + 2)))
    for r, line in enumerate(lines):
        offset = (r + 1) * W2 + 1
        grid[offset:offset + len(line)] = line
    start = grid.find(b'S')
    end = grid.find(b'E')
    if start == -1 or end == -1:
        return -1
    if start == end:
        return 0
    wall = ord('#')
    grid[start] = wall
    grid[end] = ord('.')
    q = deque([start])
    dist = 0
    while q:
        dist += 1
        for _ in range(len(q)):
            u = q.popleft()
            for v in (u - 1, u + 1, u - W2, u + W2):
                if grid[v] != wall:
                    if v == end:
                        return dist
                    grid[v] = wall
                    q.append(v)
    return -1

def generate_maze_2000(seed, density=0.28, unreachable=False):
    rng = random.Random(seed)
    H, W = 2000, 2000
    # Fast generation using byte chunks
    chunk = bytearray(b'.' * 10000)
    for i in range(10000):
        if rng.random() < density:
            chunk[i] = ord('#')
    
    rows = []
    for r in range(H):
        offset = (r * 137) % 7000
        row = bytearray(chunk[offset:offset + W])
        # Add some per-row randomness
        for _ in range(20):
            idx = rng.randrange(W)
            row[idx] = ord('#') if rng.random() < 0.5 else ord('.')
        if r == 0 or r == H - 1:
            row[:] = b'#' * W
        else:
            row[0] = ord('#')
            row[-1] = ord('#')
        rows.append(row)
    
    # Also carve a guaranteed winding path unless unreachable
    r, c = 1, 1
    rows[r][c] = ord('S')
    while r < H - 2 or c < W - 2:
        if r < H - 2 and (c == W - 2 or rng.random() < 0.5):
            r += 1
        else:
            c += 1
        rows[r][c] = ord('.')
    rows[H - 2][W - 2] = ord('E')
    if unreachable:
        # Block around E
        rows[H - 3][W - 2] = ord('#')
        rows[H - 2][W - 3] = ord('#')
    return b'\n'.join(rows) + b'\n'

def ensure_test_data():
    if os.path.exists('test_2000_1.txt') and os.path.exists('test_meta.txt'):
        return
    m1 = generate_maze_2000(42, 0.30, False)
    m2 = generate_maze_2000(123, 0.25, False)
    m3 = generate_maze_2000(999, 0.30, True)
    ans1 = solve_ref(m1)
    ans2 = solve_ref(m2)
    ans3 = solve_ref(m3)
    with open('test_2000_1.txt', 'wb') as f:
        f.write(m1)
    with open('test_2000_2.txt', 'wb') as f:
        f.write(m2)
    with open('test_2000_3.txt', 'wb') as f:
        f.write(m3)
    with open('test_meta.txt', 'w') as f:
        f.write(f"{ans1},{ans2},{ans3}\n")

def run_maze(input_bytes):
    p = subprocess.run([sys.executable, 'maze.py'], input=input_bytes, capture_output=True)
    if p.returncode != 0:
        return None
    try:
        return int(p.stdout.strip())
    except:
        return None

def main():
    ensure_test_data()
    # Edge cases
    edges = [
        (b"S.E\n", 2),
        (b"S#E\n", -1),
        (b"SE\n", 1),
        (b"S\n.\nE\n", 2),
        (b"#####\n#S..#\n###.#\n#E..#\n#####\n", 6),
        (b"#####\n#S#E#\n#####\n", -1),
        (b"...\n.S.\n...\n", -1),
    ]
    for inp, exp in edges:
        got = run_maze(inp)
        if got != exp:
            print(0)
            sys.exit(0)

    with open('test_meta.txt') as f:
        ans1, ans2, ans3 = map(int, f.read().strip().split(','))
    with open('test_2000_1.txt', 'rb') as f:
        m1 = f.read()
    with open('test_2000_2.txt', 'rb') as f:
        m2 = f.read()
    with open('test_2000_3.txt', 'rb') as f:
        m3 = f.read()

    t0 = time.perf_counter()
    for m, exp in [(m1, ans1), (m2, ans2), (m3, ans3)]:
        got = run_maze(m)
        if got != exp:
            print(0)
            sys.exit(0)
    elapsed = time.perf_counter() - t0
    score = 1000.0 / elapsed
    print(f"{score:.2f}")

if __name__ == '__main__':
    main()
