import subprocess, sys, time

# Edge cases to verify correctness
EDGE_CASES = [
    ("SE\n", 1),
    ("S.E\n", 2),
    ("S#E\n", -1),
    ("S\n.\nE\n", 2),
    ("...\n.S.\n...\n", -1),
    ("S..#\n.##.\n....\n#..E\n", 6),
    # Snake maze without border walls
    ("S....\n####.\n.....\n.####\n....E\n", 16),
]

def verify_and_bench():
    # First test edge cases via stdin using a single worker or direct call
    import maze
    import io
    for grid, expected in EDGE_CASES:
        old_stdin, old_stdout = sys.stdin, sys.stdout
        try:
            # simulate buffer.read()
            class FakeStdin:
                def __init__(self, b):
                    self.buffer = io.BytesIO(b)
            sys.stdin = FakeStdin(grid.encode('ascii'))
            out = io.StringIO()
            sys.stdout = out
            maze.solve()
            ans = int(out.getvalue().strip())
        except Exception as e:
            print(0)
            return
        finally:
            sys.stdin, sys.stdout = old_stdin, old_stdout
        if ans != expected:
            sys.stderr.write(f"Failed edge case: got {ans}, expected {expected}\n")
            print(0)
            return

    # Now benchmark via subprocess on the generated mazes
    tests = [
        ('maze_2000.txt', 3994),
        ('maze_2000_b.txt', 3994),
        ('maze_unsolvable.txt', -1),
    ]
    t0 = time.perf_counter()
    for fname, expected in tests:
        with open(fname, 'rb') as f:
            p = subprocess.run([sys.executable, 'maze.py'], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            print(0)
            return
        try:
            ans = int(p.stdout.strip())
        except:
            print(0)
            return
        if ans != expected:
            sys.stderr.write(f"Failed {fname}: got {ans}, expected {expected}\n")
            print(0)
            return
    elapsed = time.perf_counter() - t0
    # Score is mazes per second (or 1000 / elapsed)
    print(f"{1000.0 / elapsed:.2f}")

if __name__ == '__main__':
    verify_and_bench()
