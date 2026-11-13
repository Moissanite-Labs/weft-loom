import sys
# independent flat-index pure-Python BFS (level by level)
rows = [r for r in sys.stdin.buffer.read().split(b'\n') if r]
m = len(rows[0]); W = m + 1
g = bytearray(b'#' * W + b'#'.join(rows) + b'#' * (W + 1))
s = g.index(b'S'); e = g.index(b'E')
g[s] = 35; fr = [s]; d = 0; ans = -1
while fr and ans < 0:
    d += 1; nx = []
    for c in fr:
        for nb in (c + 1, c - 1, c + W, c - W):
            if g[nb] != 35:
                g[nb] = 35; nx.append(nb)
                if nb == e: ans = d
    fr = nx
print(ans)
