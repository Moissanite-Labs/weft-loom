import sys
def main():
    lines = sys.stdin.read().split()
    h = len(lines)
    if h == 0:
        print(-1); return
    w = len(lines[0])
    W = w + 1
    g = bytearray(b'#' * W)  # sentinel border
    for l in lines:
        g += l.encode().ljust(w, b'#') + b'#'
    g += b'#' * W
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g[s] = 35
    front = [s]
    d = 0
    while front:
        d += 1
        nf = []
        ap = nf.append
        for p in front:
            for q in (p - 1, p + 1, p - W, p + W):
                c = g[q]
                if c != 35:
                    if q == e:
                        print(d); return
                    g[q] = 35
                    ap(q)
        front = nf
    print(-1)
main()
