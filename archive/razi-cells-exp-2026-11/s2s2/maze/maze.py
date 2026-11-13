import sys


def main():
    rows = sys.stdin.read().split()
    if not rows:
        print(-1)
        return
    W = max(len(r) for r in rows) + 2
    body = ['#' + r.ljust(W - 2, '#') + '#' for r in rows]
    grid = '#' * W + ''.join(body) + '#' * W
    s = grid.find('S')
    e = grid.find('E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    tbl = bytes(1 if i == 35 else 0 for i in range(256))
    seen = bytearray(grid.encode().translate(tbl))
    seen[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p - 1, p + 1, p - W, p + W):
                if not seen[q]:
                    seen[q] = 1
                    app(q)
        if seen[e]:
            print(d)
            return
        frontier = nxt
    print(-1)


main()
