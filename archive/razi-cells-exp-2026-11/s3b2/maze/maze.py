import sys
def main():
    lines = sys.stdin.read().split()
    h = len(lines)
    if h == 0:
        print(-1); return
    w = max(len(l) for l in lines) + 1
    W = w
    g = bytearray(b'#' * (W * (h + 2)))
    for i, l in enumerate(lines):
        o = (i + 1) * W
        g[o:o + len(l)] = l.encode()
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g[s] = 35
    g[e] = 46
    fr = [s]; d = 0
    while fr:
        d += 1
        nf = []
        ap = nf.append
        for p in fr:
            for q in (p - 1, p + 1, p - W, p + W):
                if g[q] == 46:
                    if q == e:
                        print(d); return
                    g[q] = 35
                    ap(q)
        fr = nf
    print(-1)
main()
