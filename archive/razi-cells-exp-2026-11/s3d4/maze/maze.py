import sys
def main():
    lines = sys.stdin.buffer.read().split()
    if not lines:
        print(-1); return
    w = max(map(len, lines)) + 2
    pad = b'#' * w
    rows = [pad]
    for l in lines:
        rows.append(b'#' + l.ljust(w - 2, b'#') + b'#')
    rows.append(pad)
    g = bytearray(b''.join(rows))
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    # blocked = '#'; mark visited by setting to '#'
    g[s] = 35
    g[e] = 46
    fr = [s]
    d = 0
    while fr:
        d += 1
        nf = []
        ap = nf.append
        for p in fr:
            q = p + 1
            if g[q] == 46:
                g[q] = 35; ap(q)
            q = p - 1
            if g[q] == 46:
                g[q] = 35; ap(q)
            q = p + w
            if g[q] == 46:
                g[q] = 35; ap(q)
            q = p - w
            if g[q] == 46:
                g[q] = 35; ap(q)
        if g[e] == 35:
            print(d); return
        fr = nf
    print(-1)
main()
