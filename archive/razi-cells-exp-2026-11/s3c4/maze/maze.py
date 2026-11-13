import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    W2 = W + 2
    g = bytearray(b'#' * (W2 * (H + 2)))
    for y, r in enumerate(rows):
        base = (y + 1) * W2 + 1
        g[base:base + len(r)] = r
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    g[s] = 35
    fr = [s]
    d = 0
    while fr:
        d += 1
        nx = []
        app = nx.append
        for i in fr:
            for j in (i - 1, i + 1, i - W2, i + W2):
                if g[j] != 35:
                    if j == e:
                        print(d)
                        return
                    g[j] = 35
                    app(j)
        fr = nx
    print(-1)


main()
