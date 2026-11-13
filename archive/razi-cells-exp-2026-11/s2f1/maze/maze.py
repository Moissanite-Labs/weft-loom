import sys


def main():
    rows = sys.stdin.read().split()
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    W2 = W + 2
    g = bytearray(b'#' * (W2 * (H + 2)))
    s = e = -1
    for i, r in enumerate(rows):
        r = r.ljust(W, '#')
        base = (i + 1) * W2 + 1
        g[base:base + W] = r.encode()
        j = r.find('S')
        if j >= 0:
            s = base + j
        j = r.find('E')
        if j >= 0:
            e = base + j
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    WALL = 35  # '#'
    g[s] = WALL
    frontier = [s]
    dist = 0
    while frontier:
        nxt = []
        app = nxt.append
        d1 = dist + 1
        for x in frontier:
            for y in (x - 1, x + 1, x - W2, x + W2):
                if g[y] != WALL:
                    if y == e:
                        print(d1)
                        return
                    g[y] = WALL
                    app(y)
        frontier = nxt
        dist = d1
    print(-1)


main()
