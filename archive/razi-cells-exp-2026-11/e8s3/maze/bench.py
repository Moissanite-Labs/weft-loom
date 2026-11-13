import subprocess
import sys
import time
import io
import maze

SMALL_TESTS = [
    (b"S.E\n", 2),
    (b"S#E\n", -1),
    (b"S#E\n...\n", 4),
    (b"#####\n#S..#\n###.#\n#E..#\n#####\n", 6),
    (b"...\n.S.\n...\n", -1),
    (b"E.S\n", 2),
    (b"SE\n", 1),
    (b"S\n.\nE\n", 2),
]

LARGE_TESTS = [
    ('maze2000_1.txt', 3996),
    ('maze2000_2.txt', 53664),
    ('maze2000_unreach.txt', -1),
]

def run_inproc(data):
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    try:
        buf_in = io.BytesIO(data)
        sys.stdin = io.TextIOWrapper(buf_in, encoding='ascii')
        buf_out = io.StringIO()
        sys.stdout = buf_out
        maze.solve()
        return int(buf_out.getvalue().strip())
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout

def main():
    # Verify small tests including CLI subprocess execution
    for data, expected in SMALL_TESTS:
        if run_inproc(data) != expected:
            print(0)
            return
    p = subprocess.run([sys.executable, 'maze.py'], input=b"#####\n#S..#\n###.#\n#E..#\n#####\n", capture_output=True)
    if p.returncode != 0 or int(p.stdout.strip()) != 6:
        print(0)
        return

    loaded = []
    for fname, expected in LARGE_TESTS:
        with open(fname, 'rb') as f:
            loaded.append((f.read(), expected))

    t0 = time.perf_counter()
    for data, expected in loaded:
        ans = run_inproc(data)
        if ans != expected:
            sys.stderr.write(f"Expected {expected}, got {ans}\n")
            print(0)
            return
    elapsed = time.perf_counter() - t0
    # Score is mazes per second * 100
    print(f"{300.0 / elapsed:.2f}")

if __name__ == '__main__':
    main()
