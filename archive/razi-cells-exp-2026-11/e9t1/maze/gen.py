import random, sys
from collections import deque

def make_maze(H, W, seed, density=0.28):
    rng = random.Random(seed)
    # Generate using numpy if large for speed
    import numpy as np
    np_rng = np.random.RandomState(seed)
    grid = np.where(np_rng.rand(H, W) < density, ord('#'), ord('.')).astype(np.uint8)
    # Ensure a Winding path exists so shortest path is non-trivial and solvable
    r, c = 1, 1
    grid[r, c] = ord('S')
    # Create some corridors and random opens
    while r < H - 2 or c < W - 2:
        if r < H - 2 and (c >= W - 2 or rng.random() < 0.5):
            r += 1
        else:
            c += 1
        grid[r, c] = ord('.')
    grid[H - 2, W - 2] = ord('E')
    grid[0, :] = ord('#')
    grid[-1, :] = ord('#')
    grid[:, 0] = ord('#')
    grid[:, -1] = ord('#')
    lines = [row.tobytes().decode('ascii') for row in grid]
    return '\n'.join(lines) + '\n'

with open('maze_2000.txt', 'w') as f:
    f.write(make_maze(2000, 2000, 42, 0.30))

with open('maze_2000_b.txt', 'w') as f:
    f.write(make_maze(2000, 2000, 123, 0.32))

with open('maze_unsolvable.txt', 'w') as f:
    m = make_maze(500, 500, 99, 0.45).splitlines()
    # block E
    row = list(m[-2])
    row[-3] = '#'
    m[-2] = ''.join(row)
    row2 = list(m[-3])
    row2[-2] = '#'
    m[-3] = ''.join(row2)
    f.write('\n'.join(m) + '\n')

