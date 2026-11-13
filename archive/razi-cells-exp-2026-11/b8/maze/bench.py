import subprocess, sys, time
import maze

EDGE_CASES = [
    (b"S\n", -1),
    (b"SE\n", 1),
    (b"S.E\n", 2),
    (b"S#E\n", -1),
    (b"S.\n#E\n", 2),
    (b"S#\n#E\n", -1),
    (b"...\n.S.\n...\n", -1),
    (b"E..S\n", 3),
    (b"S..#\r\n.##.\r\n...E\r\n", 5),
    (b"#S#\n#.#\n#E#\n", 2),
]

for raw, exp in EDGE_CASES:
    got = maze.solve(raw)
    if got != exp:
        print(0)
        sys.exit(0)

# Verify CLI stdin/stdout on a small case and a 2000x2000 case
with open("expected.txt") as f:
    exp_lines = [int(x) for x in f.read().split()]

with open("maze_2000_a.txt", "rb") as f: m_a = f.read()
with open("maze_2000_b.txt", "rb") as f: m_b = f.read()
with open("maze_2000_c.txt", "rb") as f: m_c = f.read()

p = subprocess.run([sys.executable, "maze.py"], input=m_a, capture_output=True)
if p.returncode != 0 or int(p.stdout.strip()) != exp_lines[0]:
    print(0)
    sys.exit(0)

# Measure solve speed over multiple iterations so total time is ~0.4-1.5s
t0 = time.perf_counter()
iters = 0
while time.perf_counter() - t0 < 0.5:
    r1 = maze.solve(m_a)
    r2 = maze.solve(m_b)
    r3 = maze.solve(m_c)
    if r1 != exp_lines[0] or r2 != exp_lines[1] or r3 != exp_lines[2]:
        print(0)
        sys.exit(0)
    iters += 3
elapsed = time.perf_counter() - t0
# Score = mazes solved per second
print(f"{iters / elapsed:.2f}")
