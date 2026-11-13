import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    Wp = W + 2
    buf = bytearray(b'#' * (Wp * (H + 2)))
    for i, r in enumerate(rows):
        off = (i + 1) * Wp + 1
        buf[off:off + len(r)] = r
    s = buf.find(b'S')
    e = buf.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    WALL = 35  # '#'
    vis = buf
    vis[s] = WALL
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            q = p + 1
            if vis[q] != WALL:
                if q == e:
                    print(d)
                    return
                vis[q] = WALL
                app(q)
            q = p - 1
            if vis[q] != WALL:
                if q == e:
                    print(d)
                    return
                vis[q] = WALL
                app(q)
            q = p + Wp
            if vis[q] != WALL:
                if q == e:
                    print(d)
                    return
                vis[q] = WALL
                app(q)
            q = p - Wp
            if vis[q] != WALL:
                if q == e:
                    print(d)
                    return
                vis[q] = WALL
                app(q)
        frontier = nxt
    print(-1)


main()
