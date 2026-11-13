#!/usr/bin/env python3
"""Fitness assay for maze.py.

Prints one number: solved-2000x2000-mazes per second (higher is better).
Prints 0 if any correctness check fails.

Checks:
  * ~400 random small/medium grids (incl. unreachable, no-E, CRLF, no trailing
    newline) against an independent Python BFS reference.
  * the big 2000x2000 (SEED-fixed) maze answer must match a stored answer.
Workload: R end-to-end runs of `python3 maze.py < big_maze` (heavy enough that
process start-up does not dominate).
"""
import os
import random
import subprocess
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, ".tmp")
os.makedirs(TMP, exist_ok=True)
BIG = os.path.join(TMP, "maze_big.txt")
EXP = os.path.join(TMP, "maze_big.ans")
N = 2000
SEED = 20240517
PY = sys.executable
PROG = os.path.join(HERE, "maze.py")


def make_big():
    if os.path.exists(BIG) and os.path.getsize(BIG) > 1000:
        return
    rng = random.Random(SEED)
    rows = []
    half = N // 2
    for r in range(N):
        if r % 2 == 0:
            rows.append(bytearray(b"." * N))
        else:
            row = bytearray(b"#" * N)
            row[rng.randrange(N)] = ord(".")
            for _ in range(half // 4):
                row[rng.randrange(N)] = ord(".")
            rows.append(row)
    rows[0][0] = ord("S")
    rows[N - 1][N - 1] = ord("E")
    with open(BIG, "wb") as f:
        f.write(b"\n".join(bytes(r) for r in rows) + b"\n")


def ref(rows):
    h, w = len(rows), len(rows[0])
    s = e = None
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "S":
                s = (r, c)
            elif ch == "E":
                e = (r, c)
    if s is None or e is None:
        return -1
    dist = {s: 0}
    q = deque([s])
    while q:
        p = q.popleft()
        d = dist[p]
        if p == e:
            return d
        r, c = p
        for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            nr, nc = nb
            if 0 <= nr < h and 0 <= nc < w and nb not in dist and rows[nr][nc] != "#":
                dist[nb] = d + 1
                q.append(nb)
    return -1


def run(inp):
    p = subprocess.run([PY, PROG], input=inp, stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL)
    out = p.stdout.strip()
    if p.returncode != 0 or not out:
        return None
    try:
        return int(out.split()[-1])
    except ValueError:
        return None


def fail(msg):
    print("FAIL: " + msg, file=sys.stderr)
    print(0)
    sys.exit(0)


def small_cases():
    rng = random.Random(SEED ^ 0x5EED)
    cases = []
    # a few hand-made ones
    cases.append(["S.E"])
    cases.append(["S#E"])
    cases.append(["S", ".", ".", ".", "E"])
    cases.append(["S..", "##.", "E.."])
    cases.append(["S........", "#######..", "E.......#"])
    for _ in range(140):
        h = rng.randint(1, 30)
        w = rng.randint(1, 30)
        p = rng.choice((0.1, 0.25, 0.4, 0.55))
        g = [["#" if rng.random() < p else "." for _ in range(w)] for _ in range(h)]
        cells = [(r, c) for r in range(h) for c in range(w)]
        if len(cells) < 2:
            continue
        a, b = rng.sample(cells, 2)
        if a == b:
            continue
        g[a[0]][a[1]] = "S"
        g[b[0]][b[1]] = "E"
        cases.append(["".join(row) for row in g])
    # a couple of larger ones (still cheap in Python reference)
    for _ in range(4):
        h = w = 120
        p = rng.choice((0.15, 0.3, 0.45))
        g = [["#" if rng.random() < p else "." for _ in range(w)] for _ in range(h)]
        g[0][0] = "S"
        g[h - 1][w - 1] = "E"
        cases.append(["".join(row) for row in g])
    # no E / no S
    cases.append(["S....", "....."])
    cases.append([".....", "....."])
    return cases


def main():
    make_big()
    # correctness on small cases
    for rows in small_cases():
        inp = ("\n".join(rows) + "\n").encode()
        exp = ref(rows)
        got = run(inp)
        if got != exp:
            fail("small case mismatch: exp %r got %r rows=%r" % (exp, got, rows[:6]))
        # no trailing newline / CRLF variants
        if run("\n".join(rows).encode()) != exp:
            fail("no-newline mismatch")
        if len(rows) <= 2 and run(("\r\n".join(rows) + "\r\n").encode()) != exp:
            fail("crlf mismatch")

    # warm up: also triggers one-time compilation of the C kernel
    with open(BIG, "rb") as f:
        big = f.read()
    got = run(big)
    if got is None or got < 0:
        fail("big maze produced no valid answer")
    if os.path.exists(EXP):
        with open(EXP) as f:
            exp = int(f.read().strip())
        if got != exp:
            fail("big maze answer changed: exp %d got %d" % (exp, got))
    else:
        with open(EXP, "w") as f:
            f.write(str(got))
    again = run(big)
    if again != got:
        fail("big maze answer unstable")

    # timed workload: end-to-end runs on the 2000x2000 maze
    R = 8
    t0 = time.perf_counter()
    for _ in range(R):
        with open(BIG, "rb") as f:
            p = subprocess.run([PY, PROG], stdin=f, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    dt = time.perf_counter() - t0
    if p.returncode != 0:
        fail("timed run failed")
    print("%.4f" % (R / dt))


if __name__ == "__main__":
    import time  # noqa: E402  (kept local to main use)
    main()
