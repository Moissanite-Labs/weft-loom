import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    W = max(len(r) for r in rows)
    W2 = W + 2
    pad = b'#' * W2
    g = bytearray(pad)
    for r in rows:
        g += b'#' + r.ljust(W, b'#') + b'#'
    g += pad
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    vis = bytearray(g.translate(bytes(1 if c == 35 else 0 for c in range(256))))
    vis[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            q = p - 1
            if not vis[q]:
                if q == e:
                    print(d)
                    return
                vis[q] = 1
                app(q)
            q = p + 1
            if not vis[q]:
                if q == e:
                    print(d)
                    return
                vis[q] = 1
                app(q)
            q = p - W2
            if not vis[q]:
                if q == e:
                    print(d)
                    return
                vis[q] = 1
                app(q)
            q = p + W2
            if not vis[q]:
                if q == e:
                    print(d)
                    return
                vis[q] = 1
                app(q)
        frontier = nxt
    print(-1)


main()
