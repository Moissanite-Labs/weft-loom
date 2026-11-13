import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read()
    lines = data.split(b"\n")
    rows = [l.rstrip(b"\r") for l in lines if l.rstrip(b"\r")]
    if not rows:
        print(-1)
        return
    w = max(len(r) for r in rows) + 2
    grid = bytearray(b"#" * (w * (len(rows) + 2)))
    s = e = -1
    for y, r in enumerate(rows):
        base = (y + 1) * w + 1
        grid[base:base + len(r)] = r
        i = r.find(b"S")
        if i >= 0:
            s = base + i
        j = r.find(b"E")
        if j >= 0:
            e = base + j
    if s < 0 or e < 0:
        print(-1)
        return
    # cells that are '.', 'S', 'E' are open
    for k in range(len(grid)):
        c = grid[k]
        if c != 35 and c != 46 and c != 83 and c != 69:
            grid[k] = 35
    if s == e:
        print(0)
        return
    grid[s] = 35
    frontier = [s]
    dist = 0
    while frontier:
        dist += 1
        nxt = []
        for p in frontier:
            for q in (p - 1, p + 1, p - w, p + w):
                c = grid[q]
                if c == 46:
                    grid[q] = 35
                    nxt.append(q)
                elif c == 69:
                    print(dist)
                    return
        frontier = nxt
    print(-1)


main()
