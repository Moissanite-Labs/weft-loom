import sys

def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    W = max(len(r) for r in rows)
    Wp = W + 2
    pad = b'#' * Wp
    buf = b''.join([pad] + [b'#' + r.ljust(W, b'#') + b'#' for r in rows] + [pad])
    s = buf.find(b'S')
    e = buf.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    tbl = bytes(1 if i == 35 else 0 for i in range(256))
    blocked = bytearray(buf.translate(tbl))
    blocked[s] = 1
    dist = 0
    frontier = [s]
    while frontier:
        dist += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p - 1, p + 1, p - Wp, p + Wp):
                if not blocked[q]:
                    if q == e:
                        print(dist)
                        return
                    blocked[q] = 1
                    app(q)
        frontier = nxt
    print(-1)

main()
