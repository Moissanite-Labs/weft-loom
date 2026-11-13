import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    W = max(len(r) for r in rows)
    P = W + 2
    border = b'#' * P
    grid = border + b''.join(b'#' + r.ljust(W, b'#') + b'#' for r in rows) + border
    s = grid.find(b'S')
    e = grid.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    t = bytes(1 if i == 35 else 0 for i in range(256))
    vis = bytearray(grid.translate(t))
    vis[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            q = p - 1
            if not vis[q]:
                vis[q] = 1
                app(q)
            q = p + 1
            if not vis[q]:
                vis[q] = 1
                app(q)
            q = p - P
            if not vis[q]:
                vis[q] = 1
                app(q)
            q = p + P
            if not vis[q]:
                vis[q] = 1
                app(q)
        d += 1
        if vis[e]:
            print(d)
            return
        frontier = nxt
    print(-1)


if __name__ == "__main__":
    main()
