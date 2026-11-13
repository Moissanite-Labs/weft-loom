import numpy as np

def make_maze(H, W, seed, p=0.75, ensure_path=False):
    rng = np.random.default_rng(seed)
    grid = np.where(rng.random((H, W)) < p, ord('.'), ord('#')).astype(np.uint8)
    grid[0, :] = ord('#')
    grid[-1, :] = ord('#')
    grid[:, 0] = ord('#')
    grid[:, -1] = ord('#')
    # Clear small area around start and end
    grid[1:5, 1:5] = ord('.')
    grid[H-5:H-1, W-5:W-1] = ord('.')
    if ensure_path:
        # Carve a winding corridor so a long path is guaranteed to exist
        for r in range(1, H-1, 40):
            grid[r, 1:W-1] = ord('.')
            if r + 20 < H - 1:
                grid[r:min(r+41, H-1), W-2 if (r//40)%2==0 else 1] = ord('.')
    grid[1, 1] = ord('S')
    grid[H-2, W-2] = ord('E')
    return b'\n'.join(row.tobytes() for row in grid) + b'\n'

if __name__ == '__main__':
    with open('maze1.txt', 'wb') as f:
        f.write(make_maze(2000, 2000, 42, 0.72, ensure_path=False))
    with open('maze2.txt', 'wb') as f:
        f.write(make_maze(2000, 2000, 123, 0.62, ensure_path=True))
    with open('maze3.txt', 'wb') as f:
        f.write(make_maze(2000, 2000, 999, 0.55, ensure_path=False))
