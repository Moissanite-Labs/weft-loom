import random, time, subprocess, sys

def make_solvable_maze(n, seed, density=0.28):
    rng = random.Random(seed)
    # Use a Winding path + random open cells to guarantee a long path and explore most of the 2000x2000 grid
    grid = [bytearray(b'.' * n) for _ in range(n)]
    # Add random walls
    for r in range(n):
        row = grid[r]
        # snake barriers every 4 rows to force long winding shortest path
        if r % 4 == 1 and r < n - 1:
            for c in range(n - 10):
                row[c] = 35
        elif r % 4 == 3 and r < n - 1:
            for c in range(10, n):
                row[c] = 35
    # Sprinkle some random walls and holes in barriers
    for _ in range(n * n // 10):
        r = rng.randrange(n)
        c = rng.randrange(n)
        if r % 4 not in (1, 3):
            grid[r][c] = 35
    grid[0][0] = ord('S')
    grid[n-1][n-1] = ord('E')
    return b'\n'.join(grid) + b'\n'

m1 = make_solvable_maze(2000, 42)
with open('maze2000_solvable.txt', 'wb') as f:
    f.write(m1)

t0 = time.perf_counter()
res = subprocess.run([sys.executable, 'maze.py'], input=m1, capture_output=True)
dt = time.perf_counter() - t0
print("Solvable output:", res.stdout.decode().strip(), "Time:", f"{dt:.4f}s")
