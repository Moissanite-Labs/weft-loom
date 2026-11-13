import sys
def main():
    lines = sys.stdin.read().split()
    if not lines:
        print(-1); return
    w = max(map(len, lines)) + 1
    g = bytearray(b'#' * (w * (len(lines) + 2)))
    for i, l in enumerate(lines):
        o = (i + 1) * w
        g[o:o + len(l)] = l.encode()
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g[s] = 35
    fr = [s]; d = 0
    ds = (1, -1, w, -w)
    while fr:
        d += 1
        nf = []
        ap = nf.append
        for p in fr:
            for k in ds:
                q = p + k
                c = g[q]
                if c != 35:
                    if c == 69:
                        print(d); return
                    g[q] = 35
                    ap(q)
        fr = nf
    print(-1)
main()
