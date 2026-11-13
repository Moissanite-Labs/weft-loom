import random, time, subprocess, os

def generate_mazes():
    if os.path.exists('maze_2000_1.txt') and os.path.exists('maze_2000_2.txt') and os.path.exists('maze_2000_3.txt'):
        return
    # Maze 1: 2000x2000 random percolation with guaranteed path (seed 42)
    rng = random.Random(42)
    H, W = 2000, 2000
    lines = []
    for r in range(H):
        b = rng.randbytes(W)
        lines.append(bytearray(35 if x < 72 else 46 for x in b))
    cr, cc = 1, 1
    for tr, tc in [(H//2, W//4), (H//4, 3*W//4), (3*H//4, W//2), (H-2, W-2)]:
        while cr != tr:
            cr += 1 if tr > cr else -1
            lines[cr][cc] = 46
        while cc != tc:
            cc += 1 if tc > cc else -1
            lines[cr][cc] = 46
    lines[1][1] = ord('S')
    lines[H-2][W-2] = ord('E')
    with open('maze_2000_1.txt', 'wb') as f:
        f.write(b'\n'.join(lines) + b'\n')

    # Maze 2: 2000x2000 snake/comb with cross-links (seed 101, longer path)
    rng = random.Random(101)
    lines2 = []
    for r in range(H):
        if r % 4 == 0 or r == H - 1:
            lines2.append(bytearray(b'#' * W))
        elif r % 2 == 1:
            lines2.append(bytearray(b'#' + b'.' * (W - 2) + b'#'))
        else:
            b = rng.randbytes(W)
            row = bytearray(35 if x < 230 else 46 for x in b)
            row[0] = 35
            row[-1] = 35
            if (r // 2) % 2 == 1:
                row[W - 2] = 46
            else:
                row[1] = 46
            lines2.append(row)
    for r in range(4, H - 1, 4):
        lines2[r][1 if (r // 4) % 2 == 0 else W - 2] = 46
        for _ in range(8):
            c = rng.randint(2, W - 3)
            lines2[r][c] = 46
    lines2[1][1] = ord('S')
    lines2[H - 3][W - 2] = ord('E')
    with open('maze_2000_2.txt', 'wb') as f:
        f.write(b'\n'.join(lines2) + b'\n')

    # Maze 3: 2000x2000 unsolvable (E walled off at end, S explores giant component)
    lines3 = [bytearray(row) for row in lines]
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        lines3[H-2+dr][W-2+dc] = 35
    with open('maze_2000_3.txt', 'wb') as f:
        f.write(b'\n'.join(lines3) + b'\n')

SMALL_TESTS = [
    (b"S.E\n", 2),
    (b"SE\n", 1),
    (b"S#E\n", -1),
    (b"S..#\n.##.\n..#E\n....\n", 7),
    (b"#####\n#S..#\n###.#\n#E..#\n#####\n", 6),
    (b"#####\n#S#E#\n#####\n", -1),
    (b".S.\r\n...\r\n.E.\r\n", 2),
]

EXPECTED_2000 = {
    'maze_2000_1.txt': 3994,
    'maze_2000_2.txt': 45533,
    'maze_2000_3.txt': -1,
}

def main():
    generate_mazes()
    for data, exp in SMALL_TESTS:
        res = subprocess.run(['python3', 'maze.py'], input=data, capture_output=True)
        if res.returncode != 0:
            print(0)
            return
        try:
            ans = int(res.stdout.decode().strip())
        except Exception:
            print(0)
            return
        if ans != exp:
            print(0)
            return

    mazes = [(fn, open(fn, 'rb').read(), EXPECTED_2000[fn]) for fn in ('maze_2000_1.txt', 'maze_2000_2.txt', 'maze_2000_3.txt')]
    t0 = time.perf_counter()
    for fn, data, exp in mazes:
        res = subprocess.run(['python3', 'maze.py'], input=data, capture_output=True)
        if res.returncode != 0:
            print(0)
            return
        try:
            ans = int(res.stdout.decode().strip())
        except Exception:
            print(0)
            return
        if ans != exp:
            print(0)
            return
    dt = time.perf_counter() - t0
    print(f"{1000.0 / dt:.2f}")

if __name__ == '__main__':
    main()
