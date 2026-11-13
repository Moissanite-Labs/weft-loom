import sys


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        print(-1)
        return
    W = max(len(r) for r in data)
    P = W + 2
    pad = b'#' * P
    g = pad + b''.join(b'#' + r.ljust(W, b'#') + b'#' for r in data) + pad
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    tbl = bytes(1 if i == 35 else 0 for i in range(256))
    seen = bytearray(g.translate(tbl))
    seen[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for v in frontier:
            for u in (v - 1, v + 1, v - P, v + P):
                if not seen[u]:
                    if u == e:
                        print(d)
                        return
                    seen[u] = 1
                    app(u)
        frontier = nxt
    print(-1)


main()
