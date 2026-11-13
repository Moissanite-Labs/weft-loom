import random, collections

def solve_ref(grid_str):
    lines = [l for l in grid_str.splitlines() if l]
    H = len(lines)
    W = len(lines[0])
    s = e = None
    for r, row in enumerate(lines):
        if 'S' in row: s = (r, row.index('S'))
        if 'E' in row: e = (r, row.index('E'))
    if not s or not e: return -1
    if s == e: return 0
    q = collections.deque([(s[0], s[1], 0)])
    vis = [bytearray(W) for _ in range(H)]
    vis[s[0]][s[1]] = 1
    while q:
        r, c, d = q.popleft()
        nd = d + 1
        for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if 0 <= nr < H and 0 <= nc < W and not vis[nr][nc] and lines[nr][nc] != '#':
                if (nr, nc) == e:
                    return nd
                vis[nr][nc] = 1
                q.append((nr, nc, nd))
    return -1

# Small tests
small_tests = [
    ("S.E\n.#.\n...\n", 2),
    ("S#E\n###\n...\n", -1),
    ("S...#\n.###.\n...#.\n.#...\n...#E\n", 8),
    ("SE\n", 1),
    (".\nS\n.\n#\nE\n", -1),
]

for i, (g, ans) in enumerate(small_tests):
    assert solve_ref(g) == ans, f"Failed ref on {i}"
    with open(f"small_{i}.txt", "w") as f:
        f.write(g)

# Generate 2000x2000 maze with fixed seed 42
rng = random.Random(42)
H = W = 2000
# Create a grid with 28% '#' obstacles and some long walls to force winding
grid = []
for r in range(H):
    # fast random row generation
    row = bytearray(b'.' * W)
    # add ~25% random walls
    for c in rng.sample(range(W), W // 4):
        row[c] = ord('#')
    # add horizontal barrier with gaps every 50 rows
    if r % 50 == 25:
        for c in range(W):
            if (c // 20) != (r % 97):
                row[c] = ord('#')
            else:
                row[c] = ord('.')
    grid.append(row)

grid[1][1] = ord('S')
grid[H-2][W-2] = ord('E')
# Ensure around S and E are open
for dr in (-1,0,1):
    for dc in (-1,0,1):
        if (dr, dc) != (0, 0):
            grid[1+dr][1+dc] = ord('.')
            grid[H-2+dr][W-2+dc] = ord('.')

maze_str = "\n".join(row.decode('ascii') for row in grid) + "\n"
with open("maze2000.txt", "w") as f:
    f.write(maze_str)

ans2000 = solve_ref(maze_str)
print("maze2000 answer:", ans2000)

# Also create an unreachable 2000x2000 maze (surround E with '#')
grid[H-3][W-2] = ord('#')
grid[H-1][W-2] = ord('#')
grid[H-2][W-3] = ord('#')
grid[H-2][W-1] = ord('#')
maze_unreach = "\n".join(row.decode('ascii') for row in grid) + "\n"
with open("maze2000_unreach.txt", "w") as f:
    f.write(maze_unreach)
ans_unreach = solve_ref(maze_unreach)
print("maze2000_unreach answer:", ans_unreach)

with open("expected.txt", "w") as f:
    f.write(f"{ans2000}\n{ans_unreach}\n")
