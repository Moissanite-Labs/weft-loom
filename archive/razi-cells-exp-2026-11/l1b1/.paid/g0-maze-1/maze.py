import sys

def main():
    rows = sys.stdin.read().split()
    if not rows:
        print(-1)
        return
    W = max(len(r) for r in rows) + 2
    lines = ['#' * W] + [('#' + r.ljust(W - 2, '#') + '#') for r in rows] + ['#' * W]
    g = ''.join(lines).encode()
    N = len(g)
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    table = bytes(1 if c == 35 else 0 for c in range(256))
    vis = bytearray(g.translate(table))
    vis[s] = 1
    front = [s]
    d = 0
    while front:
        d += 1
        nf = []
        app = nf.append
        for i in front:
            for j in (i - 1, i + 1, i - W, i + W):
                if not vis[j]:
                    if j == e:
                        print(d)
                        return
                    vis[j] = 1
                    app(j)
        front = nf
    print(-1)

main()
