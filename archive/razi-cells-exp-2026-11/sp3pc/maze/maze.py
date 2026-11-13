import sys

def main():
    rows = sys.stdin.read().split()
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    PW = W + 2
    N = (H + 2) * PW
    wall = bytearray(b'\x01') * N
    TBL = bytes(1 if k == 35 else 0 for k in range(256))
    s = e = -1
    for i, r in enumerate(rows):
        base = (i + 1) * PW + 1
        rb = r.encode('latin-1', 'replace')
        wall[base:base + len(rb)] = rb.translate(TBL)
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
    seen = wall
    seen[s] = 1
    frontier = [s]
    d = 0
    offs = (-PW, PW, -1, 1)
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            for o in offs:
                q = p + o
                if not seen[q]:
                    if q == e:
                        print(d)
                        return
                    seen[q] = 1
                    app(q)
        frontier = nxt
    print(-1)

main()
