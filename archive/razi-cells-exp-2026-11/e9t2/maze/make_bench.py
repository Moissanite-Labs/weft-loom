import random, time, subprocess

def make_maze(H, W, seed, solvable=True):
    rng = random.Random(seed)
    # Generate a fast random maze with ~70% open cells or spanning corridors + loops
    # To make BFS do substantial work on 2000x2000, let's create a maze with winding paths and open areas
    row_bytes = bytearray(b'.' * W)
    lines = []
    # Use random bytes to quickly build rows
    for r in range(H):
        b = bytearray(rng.randbytes(W))
        # threshold ~ 75/256 walls (~29% walls, below percolation threshold 0.407 so giant component exists)
        line = bytes(35 if x < 72 else 46 for x in b)
        lines.append(bytearray(line))
    # Guarantee a long winding path so it's solvable if solvable=True, or block E if not
    r, c = 1, 1
    lines[r][c] = ord('S')
    if solvable:
        # carve a sneaky path along some waypoints so it is guaranteed connected, plus random percolation
        cr, cc = r, c
        waypoints = [(H//2, W//4), (H//4, 3*W//4), (3*H//4, W//2), (H-2, W-2)]
        for tr, tc in waypoints:
            while cr != tr:
                cr += 1 if tr > cr else -1
                lines[cr][cc] = ord('.')
            while cc != tc:
                cc += 1 if tc > cc else -1
                lines[cr][cc] = ord('.')
        lines[1][1] = ord('S')
        lines[H-2][W-2] = ord('E')
    else:
        lines[H-2][W-2] = ord('E')
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            lines[H-2+dr][W-2+dc] = ord('#')
    return b'\n'.join(lines) + b'\n'

t0 = time.perf_counter()
m1 = make_maze(2000, 2000, 42, True)
m2 = make_maze(2000, 2000, 43, False)
with open('maze_2000_solvable.txt', 'wb') as f:
    f.write(m1)
with open('maze_2000_unsolvable.txt', 'wb') as f:
    f.write(m2)
print(f"Generated 2000x2000 mazes in {time.perf_counter()-t0:.2f}s")

for fname in ['maze_2000_solvable.txt', 'maze_2000_unsolvable.txt']:
    t0 = time.perf_counter()
    res = subprocess.run(['python3', 'maze.py'], input=open(fname, 'rb').read(), capture_output=True)
    dt = time.perf_counter() - t0
    print(fname, "ans:", res.stdout.decode().strip(), f"time: {dt:.3f}s")
