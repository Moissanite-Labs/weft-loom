#!/usr/bin/env python3
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
MAZE = os.path.join(HERE, '.bench_maze.txt')
EXP = os.path.join(HERE, '.bench_expected.txt')

def main():
    if not os.path.exists(MAZE):
        subprocess.run([sys.executable, os.path.join(HERE, 'gen.py'),
                        '2000', '2000', '2024', MAZE], check=True)
    if not os.path.exists(EXP):
        with open(MAZE, 'rb') as f:
            p = subprocess.run([sys.executable, os.path.join(HERE, 'ref.py')],
                               stdin=f, stdout=subprocess.PIPE, check=True)
        with open(EXP, 'wb') as f:
            f.write(p.stdout)
    expected = open(EXP).read().strip()
    with open(MAZE, 'rb') as f:
        data = f.read()
    best = 1e9
    reps = 15
    for i in range(reps):
        t = time.perf_counter()
        p = subprocess.run([sys.executable, os.path.join(HERE, 'maze.py')],
                           input=data, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL)
        dt = time.perf_counter() - t
        out = p.stdout.decode().strip()
        if p.returncode != 0 or out != expected:
            print(0)
            return
        if dt < best:
            best = dt
    # higher is better; ~40ms -> ~25000
    print(round(1000.0 / best, 2))

if __name__ == '__main__':
    main()
