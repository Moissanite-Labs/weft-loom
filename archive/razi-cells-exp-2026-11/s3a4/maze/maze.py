import sys


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        print(-1)
        return
    W = len(data[0]) + 2
    # pad with a '#' border so neighbours never need bounds checks
    g = b'#' * W + b''.join(b'#' + r + b'#' for r in data) + b'#' * W
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    tbl = bytes(1 if c == 35 else 0 for c in range(256))  # '#' -> already seen
    seen = bytearray(g.translate(tbl))
    seen[s] = 1
    frontier = [s]
    d = 0
    offs = (1, -1, W, -W)
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            for o in offs:
                q = p + o
                if not seen[q]:
                    if q == e:
                        print(d)
                        return
                    seen[q] = 1
                    app(q)
        frontier = nxt
    print(-1)


main()
