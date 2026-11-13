import sys


def main():
    rows = sys.stdin.read().split()
    if not rows:
        print(-1)
        return
    W = max(len(r) for r in rows)
    W2 = W + 2
    border = b'#' * W2
    body = b''.join(b'#' + r.encode().ljust(W, b'#') + b'#' for r in rows)
    buf = border + body + border
    s = buf.find(b'S')
    e = buf.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    tbl = bytes(1 if i == 35 else 0 for i in range(256))
    vis = bytearray(buf.translate(tbl))
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
