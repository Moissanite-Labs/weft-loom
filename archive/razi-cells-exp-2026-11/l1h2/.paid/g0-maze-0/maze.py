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
    buf[s] = 35
    frontier = [s]
    d = 0
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p - 1, p + 1, p - Wp, p + Wp):
                if buf[q] != 35:
                    if q == e:
                        print(d + 1)
                        return
                    buf[q] = 35
                    app(q)
        frontier = nxt
        d += 1
    print(-1)


main()
