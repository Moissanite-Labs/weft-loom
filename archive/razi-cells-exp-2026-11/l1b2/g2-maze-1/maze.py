import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    w = len(rows[0])
    h = len(rows)
    W = w + 2
    g = bytearray(b'#' * (W * (h + 2)))
    for i, r in enumerate(rows):
        base = (i + 1) * W + 1
        g[base:base + w] = r[:w]
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
        push = nxt.append
        for p in frontier:
            q = p - 1
            c = g[q]
            if c != 35:
                if c == 69:
                    print(d)
                    return
                g[q] = 35
                push(q)
            q = p + 1
            c = g[q]
            if c != 35:
                if c == 69:
                    print(d)
                    return
                g[q] = 35
                push(q)
            q = p - W
            c = g[q]
            if c != 35:
                if c == 69:
                    print(d)
                    return
                g[q] = 35
                push(q)
            q = p + W
            c = g[q]
            if c != 35:
                if c == 69:
                    print(d)
                    return
                g[q] = 35
                push(q)
        frontier = nxt
    print(-1)


main()
