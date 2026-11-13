import subprocess, sys, time, os
here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
def run(prog, path):
    with open(path, 'rb') as f:
        return subprocess.run([sys.executable, prog], stdin=f, capture_output=True, timeout=25).stdout.decode().strip()
try:
    # correctness: small cases against the reference, big case against stored answer
    for p in ('s.txt', 't.txt'):
        if run('maze.py', p) != run('ref.py', p):
            print(0); sys.exit(0)
    want = open('big.ans').read().strip()
    N = 10
    t = time.perf_counter()
    for _ in range(N):
        if run('maze.py', 'big.txt') != want:
            print(0); sys.exit(0)
    dt = time.perf_counter() - t
    print(round(N / dt, 3))  # runs per second on the 2000x2000 maze
except Exception:
    print(0)
