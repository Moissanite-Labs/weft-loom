import sys
def main():
    lines = sys.stdin.read().split()
    w = max(map(len, lines)) + 2
    g = bytearray(b'#' * w)
    for l in lines:
        g += b'#' + l.encode().ljust(w - 2, b'#') + b'#'
    g += b'#' * w
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g[s] = 35
    f = [s]; d = 0
    while f:
        d += 1
        n = []
        a = n.append
        for p in f:
            for q in (p + 1, p - 1, p + w, p - w):
                c = g[q]
                if c == 46:
                    g[q] = 35; a(q)
                elif c == 69:
                    print(d); return
        f = n
    print(-1)
main()
