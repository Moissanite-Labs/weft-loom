import sys


def main():
    rows = [r for r in sys.stdin.read().split() if r]
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    Wp = W + 2
    N = Wp * (H + 2)
    table = bytes(1 if c == 35 else 0 for c in range(256))
    vis = bytearray(b'\x01') * N
    s = e = -1
    for i, r in enumerate(rows):
        base = (i + 1) * Wp + 1
        b = r.encode()
        vis[base:base + len(b)] = b.translate(table)
        j = r.find('S')
        if j >= 0:
            s = base + j
        j = r.find('E')
        if j >= 0:
            e = base + j
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    vis[s] = 1
    frontier = [s]
    d = 0
    up = -Wp
    dn = Wp
    while frontier:
        d += 1
        nxt = []
        push = nxt.append
        for p in frontier:
            q = p - 1
            if not vis[q]:
                if q == e:
                    print(d)
                    return
                vis[q] = 1
                push(q)
            q = p + 1
            if not vis[q]:
                if q == e:
                    print(d)
                    return
                vis[q] = 1
                push(q)
            q = p + up
            if not vis[q]:
                if q == e:
                    print(d)
                    return
                vis[q] = 1
                push(q)
            q = p + dn
            if not vis[q]:
                if q == e:
                    print(d)
                    return
                vis[q] = 1
                push(q)
        frontier = nxt
    print(-1)


if __name__ == "__main__":
    main()
