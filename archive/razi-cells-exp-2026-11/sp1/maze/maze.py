import sys


def main():
    rows = sys.stdin.read().split()
    if not rows:
        print(-1)
        return
    w = max(len(r) for r in rows)
    W = w + 2
    pad = ['#' * W] + ['#' + r.ljust(w, '#') + '#' for r in rows] + ['#' * W]
    g = ''.join(pad).encode()
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    tbl = bytearray(256)
    tbl[35] = 1
    seen = bytearray(g.translate(bytes(tbl)))
    seen[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        nxt = []
        push = nxt.append
        for p in frontier:
            for nb in (p - 1, p + 1, p - W, p + W):
                if not seen[nb]:
                    seen[nb] = 1
                    push(nb)
        d += 1
        if seen[e]:
            print(d)
            return
        frontier = nxt
    print(-1)


main()
