import sys

TABLE = bytes(0 if i == 35 else 1 for i in range(256))


def main():
    rows = [r for r in sys.stdin.read().split() if r]
    if not rows:
        print(-1)
        return
    W = max(len(r) for r in rows) + 2
    border = '#' * W
    padded = border + ''.join('#' + r.ljust(W - 2, '#') + '#' for r in rows) + border
    s = padded.find('S')
    e = padded.find('E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    grid = bytearray(padded.encode('latin-1').translate(TABLE))
    grid[s] = 0
    grid[e] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p - 1, p + 1, p - W, p + W):
                if grid[q]:
                    if q == e:
                        print(d)
                        return
                    grid[q] = 0
                    app(q)
        frontier = nxt
    print(-1)


main()
