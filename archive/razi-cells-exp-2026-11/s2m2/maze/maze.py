import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    W = max(len(r) for r in rows) + 2
    rows = [b'#' + r + b'#' * (W - 1 - len(r)) for r in rows]
    border = b'#' * W
    g = bytearray(b''.join([border] + rows + [border]))
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    g[s] = 35
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for i in frontier:
            for j in (i - 1, i + 1, i - W, i + W):
                c = g[j]
                if c != 35:
                    if j == e:
                        print(d)
                        return
                    g[j] = 35
                    app(j)
        frontier = nxt
    print(-1)


main()
