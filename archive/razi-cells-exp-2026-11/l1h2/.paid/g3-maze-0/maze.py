import sys
def main():
    lines = sys.stdin.buffer.read().split()
    if not lines:
        print(-1); return
    w = max(len(l) for l in lines)
    W = w + 2
    rows = [b'#' + l.ljust(w, b'#') + b'#' for l in lines]
    buf = b'#' * W + b''.join(rows) + b'#' * W
    s = buf.find(b'S'); e = buf.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g = bytearray(buf.translate(bytes.maketrans(b'#', b'\x00').replace(b'', b'') if False else _T))
    g[s] = 0
    if s == e:
        print(0); return
    fr = [s]; d = 0
    while fr:
        d += 1
        nx = []
        ap = nx.append
        for p in fr:
            q = p - 1
            if g[q]: g[q] = 0; ap(q)
            q = p + 1
            if g[q]: g[q] = 0; ap(q)
            q = p - W
            if g[q]: g[q] = 0; ap(q)
            q = p + W
            if g[q]: g[q] = 0; ap(q)
        if not g[e]:
            print(d); return
        fr = nx
    print(-1)
_T = bytes(0 if c == 35 else 1 for c in range(256))
main()
