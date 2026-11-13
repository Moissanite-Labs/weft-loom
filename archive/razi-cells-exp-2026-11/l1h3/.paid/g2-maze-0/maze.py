import sys
def main():
    lines = sys.stdin.buffer.read().split()
    if not lines:
        print(-1); return
    w = max(map(len, lines)) + 1
    g = bytearray(b'#' * (w * (len(lines) + 2)))
    for i, l in enumerate(lines):
        g[(i + 1) * w:(i + 1) * w + len(l)] = l
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g[s] = 35
    fr = [s]; d = 0
    while fr:
        d += 1
        nf = []
        ap = nf.append
        for p in fr:
            for q in (p - 1, p + 1, p - w, p + w):
                c = g[q]
                if c != 35:
                    if c == 69:
                        print(d); return
                    g[q] = 35
                    ap(q)
        fr = nf
    print(-1)
main()
