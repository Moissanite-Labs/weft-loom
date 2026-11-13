import sys
def main():
    data = sys.stdin.buffer.read().split()
    rows = [r for r in data if r]
    if not rows:
        print(-1); return
    H = len(rows); W = len(rows[0])
    WW = W + 2
    # flat grid with wall border; 0 = open, 1 = wall
    g = bytearray(b'\x01') * (WW * (H + 2))
    s = e = -1
    for i, r in enumerate(rows):
        base = (i + 1) * WW + 1
        # mark open cells: '.' 'S' 'E' -> 0
        row = r.translate(bytes.maketrans(b'.SE#', b'\x00\x00\x00\x01'))
        g[base:base + W] = row
        si = r.find(b'S')
        if si >= 0: s = base + si
        ei = r.find(b'E')
        if ei >= 0: e = base + ei
    if s < 0 or e < 0:
        print(-1); return
    if s == e:
        print(0); return
    g[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            q = p - 1
            if not g[q]:
                if q == e: print(d); return
                g[q] = 1; app(q)
            q = p + 1
            if not g[q]:
                if q == e: print(d); return
                g[q] = 1; app(q)
            q = p - WW
            if not g[q]:
                if q == e: print(d); return
                g[q] = 1; app(q)
            q = p + WW
            if not g[q]:
                if q == e: print(d); return
                g[q] = 1; app(q)
        frontier = nxt
    print(-1)
main()
