import sys
def main():
    lines = sys.stdin.read().split()
    if not lines:
        print(-1); return
    w = len(lines[0]) + 2
    g = bytearray(b'#' * w)
    for l in lines:
        g += b'#' + l.encode() + b'#'
    g += b'#' * w
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g[s] = 35
    cur = [s]; d = 0
    while cur:
        d += 1
        nxt = []
        a = nxt.append
        for p in cur:
            q = p + 1
            if g[q] != 35:
                if q == e:
                    print(d); return
                g[q] = 35; a(q)
            q = p - 1
            if g[q] != 35:
                if q == e:
                    print(d); return
                g[q] = 35; a(q)
            q = p + w
            if g[q] != 35:
                if q == e:
                    print(d); return
                g[q] = 35; a(q)
            q = p - w
            if g[q] != 35:
                if q == e:
                    print(d); return
                g[q] = 35; a(q)
        cur = nxt
    print(-1)
main()
