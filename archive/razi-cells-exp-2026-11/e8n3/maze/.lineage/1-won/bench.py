import subprocess
import time
import random
import os

def generate_maze(H, W, seed, solvable=True):
    rng = random.Random(seed)
    # Create a maze with lots of open paths and walls (~28% walls, below percolation threshold 40.7%)
    # Actually let's also carve a guaranteed winding path or check with reference BFS
    grid = bytearray(b'.' * (H * (W + 1)))
    for r in range(H):
        grid[r * (W + 1) + W] = 10 # '\n'
    
    # Random walls
    for r in range(H):
        row_off = r * (W + 1)
        # Fast random generation using randbytes
        rb = rng.randbytes(W)
        for c in range(W):
            if rb[c] < 75: # ~29.3% walls
                grid[row_off + c] = 35 # '#'
                
    if not solvable:
        # Put wall barrier
        mid = H // 2
        grid[mid * (W + 1) : mid * (W + 1) + W] = b'#' * W
        
    grid[0] = ord('S')
    grid[(H - 1) * (W + 1) + (W - 1)] = ord('E')
    return bytes(grid)

def ref_solve(data):
    lines = data.splitlines()
    H = len(lines)
    W = len(lines[0])
    stride = W + 1
    grid = bytearray(b'#'.join(lines) + b'#')
    s = grid.find(b'S')
    e = grid.find(b'E')
    if s == -1 or e == -1: return -1
    if s == e: return 0
    grid[s] = 35
    grid[e] = 46
    limit = len(grid)
    curr = [s]
    dist = 0
    while curr:
        dist += 1
        nxt = []
        for p in curr:
            for np in (p + 1, p - 1, p + stride, p - stride):
                if 0 <= np < limit and grid[np] == 46:
                    if np == e:
                        return dist
                    grid[np] = 35
                    nxt.append(np)
        curr = nxt
    return -1

def ensure_mazes():
    if os.path.exists("maze_2000_1.txt") and os.path.exists("expected.txt"):
        return
    m1 = generate_maze(2000, 2000, 42, True)
    m2 = generate_maze(2000, 2000, 1337, True)
    m3 = generate_maze(2000, 2000, 999, False)
    ans1 = ref_solve(m1)
    ans2 = ref_solve(m2)
    ans3 = ref_solve(m3)
    with open("maze_2000_1.txt", "wb") as f: f.write(m1)
    with open("maze_2000_2.txt", "wb") as f: f.write(m2)
    with open("maze_2000_3.txt", "wb") as f: f.write(m3)
    with open("expected.txt", "w") as f:
        f.write(f"{ans1}\n{ans2}\n{ans3}\n")

def run_test():
    ensure_mazes()
    with open("expected.txt") as f:
        exp = [int(x) for x in f.read().split()]
    
    # Small sanity checks
    small_tests = [
        (b"S.E\n", 2),
        (b"S#E\n", -1),
        (b"S..\n.#.\n..E\n", 4),
        (b"E..#\n.#..\n...S\n", 5),
    ]
    for inp, ans in small_tests:
        p = subprocess.run(["python3", "maze.py"], input=inp, capture_output=True)
        if p.returncode != 0 or int(p.stdout.strip()) != ans:
            print(0)
            return

    files = ["maze_2000_1.txt", "maze_2000_2.txt", "maze_2000_3.txt"]
    t0 = time.perf_counter()
    for fname, ans in zip(files, exp):
        with open(fname, "rb") as f:
            p = subprocess.run(["python3", "maze.py"], stdin=f, capture_output=True)
        if p.returncode != 0:
            print(0)
            return
        try:
            out = int(p.stdout.strip())
        except:
            print(0)
            return
        if out != ans:
            print(0)
            return
    elapsed = time.perf_counter() - t0
    # Score = mazes per second (3 mazes / elapsed) * 100
    print(f"{300.0 / elapsed:.2f}")

if __name__ == "__main__":
    run_test()
