import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    W = len(rows[0])
    H = len(rows)
    grid = b''.join(rows)
    N = H * W
    s = grid.find(b'S')
    e = grid.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    t = bytearray(256)
    t[ord('#')] = 1
    seen = bytearray(grid.translate(bytes(t)))
    seen[s] = 1
    frontier = [s]
    d = 0
    last = W - 1
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            if p == e:
                print(d)
                return
            c = p % W
            if p >= W:
                q = p - W
                if not seen[q]:
                    seen[q] = 1
                    app(q)
            if p + W < N:
                q = p + W
                if not seen[q]:
                    seen[q] = 1
                    app(q)
            if c:
                q = p - 1
                if not seen[q]:
                    seen[q] = 1
                    app(q)
            if c != last:
                q = p + 1
                if not seen[q]:
                    seen[q] = 1
                    app(q)
        frontier = nxt
        d += 1
    print(-1)


main()
