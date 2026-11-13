import sys

def main():
    rows = [r for r in sys.stdin.buffer.read().split() if r]
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    Wp = W + 2
    g = bytearray(b'#' * (Wp * (H + 2)))
    for i, r in enumerate(rows):
        base = (i + 1) * Wp + 1
        g[base:base + len(r)] = r
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    table = bytes(1 if c == 35 else 0 for c in range(256))
    vis = bytearray(g.translate(table))
    vis[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p + 1, p - 1, p + Wp, p - Wp):
                if not vis[q]:
                    vis[q] = 1
                    app(q)
        if vis[e]:
            print(d)
            return
        frontier = nxt
    print(-1)

main()
