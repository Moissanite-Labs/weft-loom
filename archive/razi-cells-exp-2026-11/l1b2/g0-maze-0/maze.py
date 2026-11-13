import sys
def main():
    lines = sys.stdin.buffer.read().split()
    if not lines:
        print(-1); return
    w = max(map(len, lines)) + 1
    g = bytearray(b'#' * (w * (len(lines) + 2)))
    for i, l in enumerate(lines):
        o = (i + 1) * w
        g[o:o + len(l)] = l
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g[s] = 35
    g[e] = 69
    fr = [s]; d = 0
    ws = -w
    while fr:
        d += 1
        nx = []
        ap = nx.append
        for p in fr:
            for q in (p + 1, p - 1, p + w, p + ws):
                c = g[q]
                if c == 46:
                    g[q] = 35; ap(q)
                elif c == 69:
                    print(d); return
        fr = nx
    print(-1)
main()
