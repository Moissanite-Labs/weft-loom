import sys
def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        print(-1); return
    w = max(len(r) for r in data)
    W = w + 1
    pad = b'#' * W
    rows = [r if len(r) == w else r.ljust(w, b'#') for r in data]
    g = pad + b'#'.join(rows) + b'#' + pad
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    if s == e:
        print(0); return
    t = bytearray(256)
    t[35] = 1
    vis = bytearray(g.translate(bytes(t)))
    vis[s] = 1
    front = [s]
    d = 0
    while front:
        d += 1
        nxt = []
        ap = nxt.append
        for p in front:
            q = p - 1
            if not vis[q]:
                vis[q] = 1; ap(q)
            q = p + 1
            if not vis[q]:
                vis[q] = 1; ap(q)
            q = p - W
            if not vis[q]:
                vis[q] = 1; ap(q)
            q = p + W
            if not vis[q]:
                vis[q] = 1; ap(q)
        if vis[e]:
            print(d); return
        front = nxt
    print(-1)
main()
