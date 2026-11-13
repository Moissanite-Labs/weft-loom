import sys


def main():
    rows = [r for r in sys.stdin.buffer.read().split() if r]
    if not rows:
        print(-1)
        return
    h = len(rows)
    w = len(rows[0])
    W = w + 2
    grid = bytearray(b'#' * (W * (h + 2)))
    s = e = -1
    for y, r in enumerate(rows):
        base = (y + 1) * W + 1
        r = r[:w]
        grid[base:base + len(r)] = r
        if s < 0:
            i = r.find(b'S')
            if i >= 0:
                s = base + i
        if e < 0:
            i = r.find(b'E')
            if i >= 0:
                e = base + i
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    table = bytes(1 if c == 35 else 0 for c in range(256))
    vis = grid.translate(table)
    vis[s] = 1
    frontier = [s]
    dist = 0
    while frontier:
        nxt = []
        push = nxt.append
        for cur in frontier:
            n = cur - W
            if not vis[n]:
                vis[n] = 1
                push(n)
            n = cur + W
            if not vis[n]:
                vis[n] = 1
                push(n)
            n = cur - 1
            if not vis[n]:
                vis[n] = 1
                push(n)
            n = cur + 1
            if not vis[n]:
                vis[n] = 1
                push(n)
        dist += 1
        if vis[e]:
            print(dist)
            return
        frontier = nxt
    print(-1)


main()
