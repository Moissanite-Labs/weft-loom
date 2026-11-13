import sys

# byte -> 1 for '#' (wall, pre-marked visited), 0 for open cell
_TBL = bytes([1 if b == 35 else 0 for b in range(256)])


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        print(-1)
        return
    H = len(data)
    W = max(len(r) for r in data)
    W2 = W + 2
    N = W2 * (H + 2)
    vis = bytearray(b'\x01') * N
    s = e = -1
    for i, r in enumerate(data):
        base = (i + 1) * W2 + 1
        vis[base:base + len(r)] = r.translate(_TBL)
        p = r.find(b'S')
        if p >= 0:
            s = base + p
        p = r.find(b'E')
        if p >= 0:
            e = base + p
    if s < 0 or e < 0:
        print(-1)
        return

    vis[s] = 1
    frontier = [s]
    d = 0
    up = W2
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            q = p - 1
            if not vis[q]:
                if q == e:
                    print(d + 1)
                    return
                vis[q] = 1
                app(q)
            q = p + 1
            if not vis[q]:
                if q == e:
                    print(d + 1)
                    return
                vis[q] = 1
                app(q)
            q = p - up
            if not vis[q]:
                if q == e:
                    print(d + 1)
                    return
                vis[q] = 1
                app(q)
            q = p + up
            if not vis[q]:
                if q == e:
                    print(d + 1)
                    return
                vis[q] = 1
                app(q)
        frontier = nxt
        d += 1
    print(-1)


main()
