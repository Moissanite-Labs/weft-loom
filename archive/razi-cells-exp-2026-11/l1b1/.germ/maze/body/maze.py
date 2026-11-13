import sys

_T = bytes(1 if i == 35 else 0 for i in range(256))


def main():
    rows = [r for r in sys.stdin.buffer.read().split() if r]
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    Wp = W + 2
    g = bytearray(b'#' * (Wp * (H + 2)))
    s = e = -1
    for i, r in enumerate(rows):
        base = (i + 1) * Wp + 1
        g[base:base + len(r)] = r
        j = r.find(b'S')
        if j >= 0:
            s = base + j
        j = r.find(b'E')
        if j >= 0:
            e = base + j
    if s < 0 or e < 0:
        print(-1)
        return
    vis = bytearray(bytes(g).translate(_T))
    vis[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            if p == e:
                print(d)
                return
            for q in (p - 1, p + 1, p - Wp, p + Wp):
                if not vis[q]:
                    vis[q] = 1
                    app(q)
        frontier = nxt
        d += 1
    print(-1)


main()
