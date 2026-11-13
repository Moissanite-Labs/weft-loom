import random, sys
from collections import deque

def solve_ref(raw_bytes):
    lines = [l for l in raw_bytes.splitlines() if l]
    if not lines: return -1
    H = len(lines)
    W = len(lines[0])
    S = E = None
    for r, row in enumerate(lines):
        s_idx = row.find(b'S')
        if s_idx != -1: S = (r, s_idx)
        e_idx = row.find(b'E')
        if e_idx != -1: E = (r, e_idx)
    if not S or not E: return -1
    if S == E: return 0
    vis = [bytearray(row) for row in lines]
    sr, sc = S
    er, ec = E
    vis[sr][sc] = 35
    q = deque([(sr, sc, 0)])
    while q:
        r, c, d = q.popleft()
        nd = d + 1
        if r > 0 and vis[r-1][c] != 35:
            if r-1 == er and c == ec: return nd
            vis[r-1][c] = 35
            q.append((r-1, c, nd))
        if r + 1 < H and vis[r+1][c] != 35:
            if r+1 == er and c == ec: return nd
            vis[r+1][c] = 35
            q.append((r+1, c, nd))
        if c > 0 and vis[r][c-1] != 35:
            if r == er and c-1 == ec: return nd
            vis[r][c-1] = 35
            q.append((r, c-1, nd))
        if c + 1 < W and vis[r][c+1] != 35:
            if r == er and c+1 == ec: return nd
            vis[r][c+1] = 35
            q.append((r, c+1, nd))
    return -1

def gen_maze(H, W, seed, extra_open=210):
    rng = random.Random(seed)
    grid = [bytearray(b'#' * W) for _ in range(H)]
    for r in range(1, H - 1, 2):
        row = grid[r]
        for c in range(1, W - 1, 2):
            row[c] = 46
            can_d = (r + 2 < H)
            can_r = (c + 2 < W)
            if can_d and can_r:
                if rng.getrandbits(1):
                    grid[r + 1][c] = 46
                else:
                    row[c + 1] = 46
            elif can_d:
                grid[r + 1][c] = 46
            elif can_r:
                row[c + 1] = 46
    for r in range(1, H - 1):
        row = grid[r]
        rb = rng.randbytes(W)
        for c in range(1, W - 1):
            if rb[c] > extra_open:
                row[c] = 46
    er = H - 2 if (H - 2) % 2 == 1 else H - 3
    ec = W - 2 if (W - 2) % 2 == 1 else W - 3
    grid[1][1] = ord('S')
    grid[er][ec] = ord('E')
    return b"\n".join(grid) + b"\n"

# 1: 2000x2000 binary tree + braiding maze (fixed seed 42)
m1 = gen_maze(2000, 2000, 42, 220)
with open("maze_2000_a.txt", "wb") as f: f.write(m1)
ans1 = solve_ref(m1)

# 2: 2000x2000 porous random obstacle grid (fixed seed 123)
rng = random.Random(123)
rows = []
for r in range(2000):
    rb = rng.randbytes(2000)
    row = bytearray(b'.' * 2000)
    for c in range(2000):
        if rb[c] < 85:
            row[c] = 35
    rows.append(row)
rows[0][0] = ord('S')
rows[1999][1999] = ord('E')
m2 = b"\n".join(rows) + b"\n"
with open("maze_2000_b.txt", "wb") as f: f.write(m2)
ans2 = solve_ref(m2)

# 3: 2000x2000 unreachable maze (fixed seed 999, blocked target)
m3_grid = bytearray(m1)
# surround E with '#'
lines3 = [bytearray(l) for l in m1.splitlines() if l]
er = 2000 - 3
ec = 2000 - 3
lines3[er-1][ec] = 35
lines3[er+1][ec] = 35
lines3[er][ec-1] = 35
lines3[er][ec+1] = 35
m3 = b"\n".join(lines3) + b"\n"
with open("maze_2000_c.txt", "wb") as f: f.write(m3)
ans3 = solve_ref(m3)

print("Answers:", ans1, ans2, ans3)
with open("expected.txt", "w") as f:
    f.write(f"{ans1}\n{ans2}\n{ans3}\n")
