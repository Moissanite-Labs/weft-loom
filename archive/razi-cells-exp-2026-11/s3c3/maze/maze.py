import sys


def main():
    rows = [r for r in sys.stdin.buffer.read().split() if r]
    if not rows:
        print(-1)
        return
    W = len(rows[0]) + 2
    border = b'#' * W
    g = bytearray(border)
    for r in rows:
        g += b'#' + r[:W - 2] + b'#'
    g += border
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    tbl = bytes(1 if c == 35 else 0 for c in range(256))
    seen = bytearray(g.translate(tbl))
    seen[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        nxt = []
        app = nxt.append
        d1 = d + 1
        for i in frontier:
            for j in (i - 1, i + 1, i - W, i + W):
                if not seen[j]:
                    if j == e:
                        print(d1)
                        return
                    seen[j] = 1
                    app(j)
        frontier = nxt
        d = d1
    print(-1)


main()
