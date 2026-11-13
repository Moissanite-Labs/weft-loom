import sys


def main():
    rows = sys.stdin.read().split()
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    W2 = W + 2
    buf = bytearray(b'#' * (W2 * (H + 2)))
    s = e = -1
    for i, r in enumerate(rows):
        base = (i + 1) * W2 + 1
        buf[base:base + W] = r.ljust(W, '#').encode()
        if s < 0:
            j = r.find('S')
            if j >= 0:
                s = base + j
        if e < 0:
            j = r.find('E')
            if j >= 0:
                e = base + j
    if s < 0 or e < 0:
        print(-1)
        return
    vis = buf.translate(bytes([1 if i == 35 else 0 for i in range(256)]))
    vis[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for n in frontier:
            for m in (n - 1, n + 1, n - W2, n + W2):
                if not vis[m]:
                    if m == e:
                        print(d)
                        return
                    vis[m] = 1
                    app(m)
        frontier = nxt
    print(-1)


main()
