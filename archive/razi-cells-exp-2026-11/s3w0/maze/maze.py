import sys


def main():
    data = sys.stdin.read().split()
    if not data:
        print(-1)
        return
    h = len(data)
    W = max(len(r) for r in data) + 2
    grid = bytearray(b'#' * ((h + 2) * W))
    for y, r in enumerate(data):
        base = (y + 1) * W + 1
        grid[base:base + len(r)] = r.encode()
    s = grid.find(b'S')
    e = grid.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    table = bytes(1 if i == 35 else 0 for i in range(256))
    vis = bytearray(grid.translate(table))
    vis[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for cur in frontier:
            for n in (cur - 1, cur + 1, cur - W, cur + W):
                if not vis[n]:
                    if n == e:
                        print(d)
                        return
                    vis[n] = 1
                    app(n)
        frontier = nxt
    print(-1)


main()
