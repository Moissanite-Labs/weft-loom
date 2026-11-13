import sys
import numpy as np

def main():
    data = sys.stdin.buffer.read().split()
    rows = [r for r in data if r]
    if not rows:
        print(-1); return
    h = len(rows); w = len(rows[0])
    W = w + 2
    buf = b''.join(rows)
    arr = np.frombuffer(buf, dtype=np.uint8).reshape(h, w)
    g = np.ones((h + 2, W), dtype=np.uint8)
    g[1:h+1, 1:w+1] = (arr == 35)
    s = buf.find(b'S'); e = buf.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    start = (s // w + 1) * W + (s % w) + 1
    end = (e // w + 1) * W + (e % w) + 1
    if start == end:
        print(0); return
    flat = g.ravel()
    flat[start] = 1
    stamp = np.zeros(flat.size, dtype=np.int64)
    offs = np.array([-1, 1, -W, W], dtype=np.int64)
    frontier = np.array([start], dtype=np.int64)
    d = 0
    while frontier.size:
        d += 1
        cand = (frontier[:, None] + offs).ravel()
        cand = cand[flat[cand] == 0]
        if cand.size == 0:
            break
        flat[cand] = 1
        if flat[end]:
            print(d); return
        if cand.size > 1:
            idx = np.arange(cand.size, dtype=np.int64)
            stamp[cand] = idx
            cand = cand[stamp[cand] == idx]
        frontier = cand
    print(-1)

main()
