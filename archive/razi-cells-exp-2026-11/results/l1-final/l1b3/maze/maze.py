import sys
def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        print(-1); return
    w = max(len(r) for r in data)
    W = w + 1
    buf = bytearray(b'#' * W)
    for r in data:
        buf += r.ljust(w, b'#') + b'#'
    buf += b'#' * W
    s = buf.find(b'S')
    e = buf.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    t = bytearray(256); t[35] = 1
    vis = bytearray(buf.translate(bytes(t)))
    vis[s] = 1
    cur = [s]
    d = 0
    while cur:
        d += 1
        nxt = []
        ap = nxt.append
        for p in cur:
            q = p + 1
            if not vis[q]:
                vis[q] = 1; ap(q)
            q = p - 1
            if not vis[q]:
                vis[q] = 1; ap(q)
            q = p + W
            if not vis[q]:
                vis[q] = 1; ap(q)
            q = p - W
            if not vis[q]:
                vis[q] = 1; ap(q)
        if vis[e]:
            print(d); return
        cur = nxt
    print(-1)
main()
