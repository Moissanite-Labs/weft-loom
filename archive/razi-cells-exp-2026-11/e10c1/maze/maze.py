import sys
TR = bytes.maketrans(b'#\n.SE', b'\x00\x00\x01\x01\x01')
def main():
    data = sys.stdin.buffer.read()
    data = data.replace(b'\r', b'')
    nl = data.find(b'\n')
    if nl < 0:
        data += b'\n'; nl = len(data) - 1
    if not data.endswith(b'\n'):
        data += b'\n'
    W = nl + 1
    s = data.find(b'S'); e = data.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g = bytearray(W) + data.translate(TR) + bytearray(W)
    s += W; e += W
    if s == e:
        print(0); return
    g[s] = 0
    g[e] = 0
    targets = [q for q in (e - W, e + W, e - 1, e + 1) if 0 <= q < len(g) and g[q]]
    if s in (e - W, e + W, e - 1, e + 1):
        print(1); return
    if not targets:
        print(-1); return
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            q = p - W
            if g[q]:
                g[q] = 0; app(q)
            q = p + W
            if g[q]:
                g[q] = 0; app(q)
            q = p - 1
            if g[q]:
                g[q] = 0; app(q)
            q = p + 1
            if g[q]:
                g[q] = 0; app(q)
        for t in targets:
            if not g[t]:
                print(d + 1); return
        frontier = nxt
    print(-1)
main()
