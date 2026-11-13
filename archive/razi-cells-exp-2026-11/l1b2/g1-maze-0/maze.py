import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    Wp = W + 2
    grid = bytearray(b'#') * (Wp * (H + 2))
    for i, r in enumerate(rows):
        base = (i + 1) * Wp + 1
        grid[base:base + len(r)] = r
    s = grid.find(b'S')
    e = grid.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    grid[s] = 35  # visited marker '#'
    frontier = [s]
    dist = 0
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p + 1, p - 1, p + Wp, p - Wp):
                c = grid[q]
                if c == 46 or c == 69:  # '.' or 'E'
                    if q == e:
                        print(dist + 1)
                        return
                    grid[q] = 35
                    app(q)
        frontier = nxt
        dist += 1
    print(-1)


main()
