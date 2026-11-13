import sys


def main():
    rows = [r for r in sys.stdin.buffer.read().split() if r]
    if not rows:
        print(-1)
        return
    W = len(rows[0]) + 2
    border = b'#' * W
    grid = bytearray(border)
    for r in rows:
        grid += b'#' + r.ljust(W - 2, b'#') + b'#'
    grid += border
    flat = bytes(grid)
    s = flat.find(b'S')
    e = flat.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    tbl = bytes(1 if i == 35 else 0 for i in range(256))
    vis = bytearray(flat.translate(tbl))
    vis[s] = 1
    frontier = [s]
    dist = 0
    while frontier:
        dist += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            q = p - 1
            if not vis[q]:
                if q == e:
                    print(dist)
                    return
                vis[q] = 1
                app(q)
            q = p + 1
            if not vis[q]:
                if q == e:
                    print(dist)
                    return
                vis[q] = 1
                app(q)
            q = p - W
            if not vis[q]:
                if q == e:
                    print(dist)
                    return
                vis[q] = 1
                app(q)
            q = p + W
            if not vis[q]:
                if q == e:
                    print(dist)
                    return
                vis[q] = 1
                app(q)
        frontier = nxt
    print(-1)


main()
