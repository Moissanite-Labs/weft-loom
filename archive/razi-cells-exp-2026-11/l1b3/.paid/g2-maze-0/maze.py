import sys
def main():
    lines = sys.stdin.buffer.read().split()
    if not lines:
        print(-1); return
    w = len(lines[0]) + 2
    data = b'#' * w + b''.join(b'#' + l + b'#' for l in lines) + b'#' * w
    s = data.find(b'S'); e = data.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    if s == e:
        print(0); return
    vis = bytearray(data.translate(bytes.maketrans(b'#', b'\x01').translate(None) if False else bytes((1 if i == 35 else 0) for i in range(256))))
    vis[s] = 1
    fr = [s]; d = 0
    while fr:
        d += 1
        nf = []
        ap = nf.append
        for p in fr:
            q = p - 1
            if not vis[q]:
                vis[q] = 1; ap(q)
            q = p + 1
            if not vis[q]:
                vis[q] = 1; ap(q)
            q = p - w
            if not vis[q]:
                vis[q] = 1; ap(q)
            q = p + w
            if not vis[q]:
                vis[q] = 1; ap(q)
        if vis[e] and e in nf:
            print(d); return
        fr = nf
    print(-1)
main()
