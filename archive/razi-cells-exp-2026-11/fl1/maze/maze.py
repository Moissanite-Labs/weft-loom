import sys


def main():
    rows = sys.stdin.read().split()
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    Wp = W + 2
    n = Wp * (H + 2)
    # seen doubles as the wall map: 1 = blocked or visited
    seen = bytearray(b'\x01' * n)
    tbl = bytes.maketrans(b'.SE#', b'\x00\x00\x00\x01')
    s = e = -1
    for i, r in enumerate(rows):
        base = (i + 1) * Wp + 1
        seen[base:base + len(r)] = r.encode().translate(tbl)
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
    seen[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            q = p - 1
            if not seen[q]:
                seen[q] = 1
                app(q)
            q = p + 1
            if not seen[q]:
                seen[q] = 1
                app(q)
            q = p - Wp
            if not seen[q]:
                seen[q] = 1
                app(q)
            q = p + Wp
            if not seen[q]:
                seen[q] = 1
                app(q)
        d += 1
        if seen[e]:
            print(d)
            return
        frontier = nxt
    print(-1)


main()
