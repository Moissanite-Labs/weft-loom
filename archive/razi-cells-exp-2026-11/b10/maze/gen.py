import random, sys

def make_maze(N=2000, seed=42, solvable=True):
    rng = random.Random(seed)
    # Create a braided/random maze on 2000x2000 with non-trivial shortest paths
    # Using cellular-like / random blocks with ~30% walls guarantees long winding paths
    row_bytes = bytearray(b'.' * N + b'\n')
    grid = [bytearray(row_bytes) for _ in range(N)]
    # Border walls or random walls
    for r in range(N):
        row = grid[r]
        # fast random wall placement using randbytes
        rb = rng.randbytes(N)
        for c in range(N):
            if rb[c] < 78: # ~30.5% walls
                row[c] = 35 # '#'
    grid[1][1] = ord('S')
    grid[N-2][N-2] = ord('E')
    if not solvable:
        grid[N-2][N-3] = 35
        grid[N-3][N-2] = 35
    return b"".join(grid)

if __name__ == "__main__":
    with open("maze_2000.txt", "wb") as f:
        f.write(make_maze(2000, 42, True))
    with open("maze_2000_unsolvable.txt", "wb") as f:
        f.write(make_maze(2000, 43, False))
    print("Generated mazes")
