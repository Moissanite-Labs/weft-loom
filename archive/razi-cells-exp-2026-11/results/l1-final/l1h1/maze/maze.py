import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    W2 = W + 2
    grid = bytearray(b'#' * (W2 * (H + 2)))
    for i, r in enumerate(rows):
        base = (i + 1) * W2 + 1
        grid[base:base + len(r)] = r
    s = grid.find(b'S')
    e = grid.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    WALL = 35  # '#'
    grid[s] = WALL
    frontier = [s]
    d = 0
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            q = p - 1
            if grid[q] != WALL:
                grid[q] = WALL
                app(q)
            q = p + 1
            if grid[q] != WALL:
                grid[q] = WALL
                app(q)
            q = p - W2
            if grid[q] != WALL:
                grid[q] = WALL
                app(q)
            q = p + W2
            if grid[q] != WALL:
                grid[q] = WALL
                app(q)
        d += 1
        if grid[e] == WALL:
            print(d)
            return
        frontier = nxt
    print(-1)


main()
