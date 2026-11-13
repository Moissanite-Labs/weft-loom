import sys
def main():
    lines = sys.stdin.read().split()
    h = len(lines)
    w = max(len(l) for l in lines)
    W = w + 1
    g = bytearray(b'#' * (W * (h + 2)))
    for i, l in enumerate(lines):
        g[(i + 1) * W:(i + 1) * W + len(l)] = l.encode()
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g[s] = 35
    g[e] = 69
    fr = [s]; d = 0
    steps = (1, -1, W, -W)
    while fr:
        d += 1
        nf = []
        ap = nf.append
        for p in fr:
            for st in steps:
                q = p + st
                c = g[q]
                if c != 35:
                    if c == 69:
                        print(d); return
                    g[q] = 35
                    ap(q)
        fr = nf
    print(-1)
main()
