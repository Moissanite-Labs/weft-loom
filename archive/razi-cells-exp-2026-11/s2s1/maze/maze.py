import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    W = len(rows[0])
    H = len(rows)
    Wp = W + 2
    buf = bytearray(b'#' * (Wp * (H + 2)))
    for i, r in enumerate(rows):
        start = (i + 1) * Wp + 1
        buf[start:start + W] = r[:W]
    s = buf.find(b'S')
    e = buf.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    seen = bytearray(buf)
    WALL = 35  # ord('#')
    seen[s] = WALL
    frontier = [s]
    d = 0
    while frontier:
        nxt = []
        for p in frontier:
            if p == e:
                print(d)
                return
            for q in (p - 1, p + 1, p - Wp, p + Wp):
                if seen[q] != WALL:
                    seen[q] = WALL
                    nxt.append(q)
        frontier = nxt
        d += 1
    print(-1)


main()
