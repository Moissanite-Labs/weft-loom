import sys
def main():
    lines = sys.stdin.read().split()
    w = len(lines[0])
    W = w + 1
    g = bytearray(('#'.join(lines) + '#').encode())
    s = g.find(b'S'); e = g.find(b'E')
    tb = bytes([0 if c != 35 else 1 for c in range(256)])
    seen = bytearray(g.translate(tb))
    seen[s] = 1
    # border: row separators are '#', pad ends with sentinels
    pad = bytearray([1]) * (W + 1)
    seen = pad + seen + pad
    off = W + 1
    s += off; e += off
    fr = [s]; d = 0
    while fr:
        d += 1
        nx = []
        a = nx.append
        for p in fr:
            q = p - 1
            if not seen[q]: seen[q] = 1; a(q)
            q = p + 1
            if not seen[q]: seen[q] = 1; a(q)
            q = p - W
            if not seen[q]: seen[q] = 1; a(q)
            q = p + W
            if not seen[q]: seen[q] = 1; a(q)
        if seen[e]:
            print(d); return
        fr = nx
    print(-1)
main()
