import sys
def main():
    lines = sys.stdin.buffer.read().split()
    h = len(lines)
    if h == 0:
        print(-1); return
    w = max(map(len, lines)) + 1
    # padded flat grid with a wall column at the end of each row and wall border rows
    g = bytearray(b'#' * (w * (h + 2)))
    for i, l in enumerate(lines):
        o = (i + 1) * w
        g[o:o + len(l)] = l
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    # wall = 35; mark visited by writing '#'
    g[s] = 35
    front = [s]
    d = 0
    while front:
        d += 1
        nxt = []
        ap = nxt.append
        for p in front:
            for q in (p - 1, p + 1, p - w, p + w):
                c = g[q]
                if c != 35:
                    if c == 69:
                        print(d); return
                    g[q] = 35
                    ap(q)
        front = nxt
    print(-1)
main()
