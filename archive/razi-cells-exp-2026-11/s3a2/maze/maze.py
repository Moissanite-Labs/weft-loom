import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    rows = [r.ljust(W, b'#') for r in rows]
    Wp = W + 2
    buf = bytearray(b'#' * (Wp * (H + 2)))
    for i, r in enumerate(rows):
        base = (i + 1) * Wp + 1
        buf[base:base + W] = r
    s = buf.find(b'S')
    e = buf.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    table = bytes(1 if c == 35 else 0 for c in range(256))  # '#' -> blocked
    seen = bytearray(buf.translate(table))
    seen[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            if p == e:
                print(d)
                return
            for q in (p - 1, p + 1, p - Wp, p + Wp):
                if not seen[q]:
                    seen[q] = 1
                    app(q)
        frontier = nxt
        d += 1
    print(-1)


main()
