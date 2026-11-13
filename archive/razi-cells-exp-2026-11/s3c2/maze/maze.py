import sys


def main():
    data = sys.stdin.read().split()
    if not data:
        print(-1)
        return
    h = len(data)
    w = max(len(r) for r in data)
    W = w + 2
    tbl = str.maketrans({'#': '\x00', '.': '\x01', 'S': '\x01', 'E': '\x01'})
    s = e = -1
    parts = [b'\x00' * W]
    for y, r in enumerate(data):
        if s < 0:
            x = r.find('S')
            if x >= 0:
                s = (y + 1) * W + x + 1
        if e < 0:
            x = r.find('E')
            if x >= 0:
                e = (y + 1) * W + x + 1
        row = r.ljust(w, '#').translate(tbl).encode('latin-1')
        parts.append(b'\x00' + row + b'\x00')
    parts.append(b'\x00' * W)
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    vis = bytearray(b''.join(parts))
    vis[s] = 0
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p - 1, p + 1, p - W, p + W):
                if vis[q]:
                    if q == e:
                        print(d)
                        return
                    vis[q] = 0
                    app(q)
        frontier = nxt
    print(-1)


main()
