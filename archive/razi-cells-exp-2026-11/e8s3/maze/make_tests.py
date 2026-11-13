import random

def gen_open_random_maze(H, W, seed, open_pct=72):
    rng = random.Random(seed)
    grid = [bytearray(b'#' * W) for _ in range(H)]
    for r in range(1, H - 1):
        grid[r][1:W-1] = bytearray(rng.choices(b'.#', weights=[open_pct, 100 - open_pct], k=W-2))
    for r in range(1, 5):
        for c in range(1, 5):
            grid[r][c] = ord('.')
            grid[H-1-r][W-1-c] = ord('.')
    grid[1][1] = ord('S')
    grid[H-2][W-2] = ord('E')
    return b'\n'.join(grid) + b'\n'

def gen_serpentine_maze(H, W, seed):
    rng = random.Random(seed)
    grid = [bytearray(b'.' * W) for _ in range(H)]
    for r in range(H):
        grid[r][0] = ord('#')
        grid[r][W-1] = ord('#')
    for c in range(W):
        grid[0][c] = ord('#')
        grid[H-1][c] = ord('#')
    for r in range(80, H - 2, 80):
        for c in range(1, W - 1):
            grid[r][c] = ord('#')
        if (r // 80) % 2 == 1:
            for c in range(W - 40, W - 20):
                grid[r][c] = ord('.')
        else:
            for c in range(20, 40):
                grid[r][c] = ord('.')
    for r in range(1, H - 1):
        if r % 80 == 0 or r in (1, H - 2):
            continue
        row = grid[r]
        for c in rng.sample(range(2, W - 2), W // 6):
            row[c] = ord('#')
    grid[1][1] = ord('S')
    grid[H-2][W-2] = ord('E')
    return b'\n'.join(grid) + b'\n'

def gen_unreach_full_explore(H, W, seed):
    data = bytearray(gen_open_random_maze(H, W, seed, open_pct=72))
    stride = W + 1
    er, ec = H - 2, W - 2
    data[(er-1)*stride + ec] = ord('#')
    data[er*stride + (ec-1)] = ord('#')
    return bytes(data)

with open('maze2000_1.txt', 'wb') as f:
    f.write(gen_open_random_maze(2000, 2000, 42, open_pct=72))

with open('maze2000_2.txt', 'wb') as f:
    f.write(gen_serpentine_maze(2000, 2000, 99))

with open('maze2000_unreach.txt', 'wb') as f:
    f.write(gen_unreach_full_explore(2000, 2000, 123))
