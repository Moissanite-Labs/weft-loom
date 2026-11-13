import subprocess, time, sys, io
import maze

# Small correctness tests (also test CLI on first two)
SMALL_TESTS = [
    ("#####\n#S..#\n###.#\n#E..#\n#####\n", "6"),
    ("#####\n#S#E#\n#####\n", "-1"),
    ("S..E\n", "3"),
    ("S\n.\nE\n", "2"),
    ("#S#\n#.#\n#E#\n", "2"),
    ("SE\n", "1"),
    ("E..S\n", "3"),
    (".S.\n###\n.E.\n", "-1"),
]

def run_cli(inp_bytes):
    p = subprocess.run([sys.executable, "maze.py"], input=inp_bytes, capture_output=True)
    if p.returncode != 0:
        return None
    return p.stdout.decode().strip()

def run_inproc(inp_bytes):
    orig_stdin = sys.stdin
    orig_stdout = sys.stdout
    try:
        buf_in = io.BytesIO(inp_bytes)
        sys.stdin = io.TextIOWrapper(buf_in)
        buf_out = io.StringIO()
        sys.stdout = buf_out
        maze.solve()
        return buf_out.getvalue().strip()
    finally:
        sys.stdin = orig_stdin
        sys.stdout = orig_stdout

# Test CLI once
if run_cli(SMALL_TESTS[0][0].encode()) != SMALL_TESTS[0][1]:
    print(0)
    sys.exit(0)

for grid, expected in SMALL_TESTS:
    out = run_inproc(grid.encode())
    if out != expected:
        print(f"FAIL small: expected {expected}, got {out}", file=sys.stderr)
        print(0)
        sys.exit(0)

LARGE_EXPECTED = [
    ("maze1.txt", "3994"),
    ("maze2.txt", "4174"),
    ("maze3.txt", "-1"),
]

datas = []
for fname, expected in LARGE_EXPECTED:
    with open(fname, "rb") as f:
        datas.append((fname, f.read(), expected))

# Run 3 iterations and take the best total_dt to reduce noise
best_total_dt = float('inf')
for _ in range(3):
    total_dt = 0.0
    for fname, data, expected in datas:
        t0 = time.perf_counter()
        out = run_inproc(data)
        dt = time.perf_counter() - t0
        if out != expected:
            print(f"FAIL {fname}: expected {expected}, got {out}", file=sys.stderr)
            print(0)
            sys.exit(0)
        total_dt += dt
    if total_dt < best_total_dt:
        best_total_dt = total_dt

print(f"{len(datas) / best_total_dt:.4f}")
