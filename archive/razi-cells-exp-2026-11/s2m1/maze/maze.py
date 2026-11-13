import sys
from collections import deque


def main():
    data = sys.stdin.read().split()
    grid = data
    if not grid:
        print(-1)
        return
    h = len(grid)
    w = len(grid[0])
    s = e = None
    for i, row in enumerate(grid):
        j = row.find('S')
        if j >= 0:
            s = (i, j)
        j = row.find('E')
        if j >= 0:
            e = (i, j)
    if s is None or e is None:
        print(-1)
        return
    if s == e:
        print(0)
        return
    # flat BFS over padded index space
    W = w + 2
    passable = bytearray((h + 2) * W)
    for i, row in enumerate(grid):
        base = (i + 1) * W + 1
        for j, ch in enumerate(row[:w]):
            if ch != '#':
                passable[base + j] = 1
    src = (s[0] + 1) * W + s[1] + 1
    dst = (e[0] + 1) * W + e[1] + 1
    dist = [-1] * ((h + 2) * W)
    dist[src] = 0
    q = deque([src])
    pop = q.popleft
    push = q.append
    while q:
        u = pop()
        if u == dst:
            print(dist[u])
            return
        d = dist[u] + 1
        for v in (u - 1, u + 1, u - W, u + W):
            if passable[v] and dist[v] < 0:
                dist[v] = d
                push(v)
    print(dist[dst])


main()
