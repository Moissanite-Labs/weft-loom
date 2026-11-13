import sys
def main():
    data = sys.stdin.read().split()
    if not data:
        print(-1); return
    h = len(data)
    w = max(len(l) for l in data)
    W = w + 1
    g = bytearray(b'#' * (W * (h + 2)))
    s = e = -1
    for i, l in enumerate(data):
        o = (i + 1) * W
        g[o:o + len(l)] = l.encode()
        j = l.find('S')
        if j >= 0: s = o + j
        j = l.find('E')
        if j >= 0: e = o + j
    if s < 0 or e < 0:
        print(-1); return
    g[s] = 35
    front = [s]
    d = 0
    while front:
        d += 1
        nxt = []
        ap = nxt.append
        for p in front:
            q = p - 1
            c = g[q]
            if c != 35:
                if c == 69:
                    print(d); return
                g[q] = 35; ap(q)
            q = p + 1
            c = g[q]
            if c != 35:
                if c == 69:
                    print(d); return
                g[q] = 35; ap(q)
            q = p - W
            c = g[q]
            if c != 35:
                if c == 69:
                    print(d); return
                g[q] = 35; ap(q)
            q = p + W
            c = g[q]
            if c != 35:
                if c == 69:
                    print(d); return
                g[q] = 35; ap(q)
        front = nxt
    print(-1)
main()
