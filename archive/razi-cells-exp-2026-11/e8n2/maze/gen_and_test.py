import random
import sys
from collections import deque

def make_maze(H, W, seed=42):
    rng = random.Random(seed)
    # Generate a non-trivial 2000x2000 maze with multiple paths and walls
    # Using randomized Prim/DFS style or dense obstacles with guaranteed long winding path + branches
    grid = [bytearray(b'#') * W for _ in range(H)]
    # Carve a winding snake with randomized corridors and cross-connections
    for r in range(1, H - 1):
        if r % 2 == 1:
            for c in range(1, W - 1):
                if rng.random() < 0.92:
                    grid[r][c] = ord('.')
        else:
            # connect rows at several points
            for _ in range(W // 20):
                c = rng.randint(1, W - 2)
                grid[r][c] = ord('.')
            # ensure at least one connection near alternating ends so it's solvable and winding
            c_end = W - 2 if (r // 2) % 2 == 1 else 1
            grid[r][c_end] = ord('.')
            for c in range(1, W - 1):
                if rng.random() < 0.35:
                    grid[r][c] = ord('.')
    grid[1][1] = ord('S')
    grid[H - 2][W - 2] = ord('E')
    return b'\n'.join(bytes(row) for row in grid) + b'\n'

data = make_maze(2000, 2000, 42)
with open('maze2000.txt', 'wb') as f:
    f.write(data)
print("Maze size:", len(data))
