import sys
def main():
    lines = sys.stdin.read().split()
    h = len(lines)
    if h == 0:
        print(-1); return
    w = len(lines[0])
    W = w + 2
    g = bytearray(b'#' * (W * (h + 2)))
    s = e = -1
    for i, l in enumerate(lines):
        b = (i + 1) * W + 1
        g[b:b + len(l)] = l.encode()
        j = l.find('S')
        if j >= 0: s = b + j
        j = l.find('E')
        if j >= 0: e = b + j
    if s < 0 or e < 0:
        print(-1); return
    g[s] = 35
    fr = [s]
    d = 0
    st = (1, -1, W, -W)
    while fr:
        d += 1
        nx = []
        ap = nx.append
        for p in fr:
            for t in st:
                q = p + t
                c = g[q]
                if c != 35:
                    if q == e:
                        print(d); return
                    g[q] = 35
                    ap(q)
        fr = nx
    print(-1)
main()
