import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    h = len(rows)
    w = max(len(r) for r in rows)
    W = w + 2
    # padded grid: border walls, 1 = visited/blocked, 0 = open
    vis = bytearray(b'\x01') * (W * (h + 2))
    s = e = -1
    for i, r in enumerate(rows):
        base = (i + 1) * W + 1
        for j, c in enumerate(r):
            if c == 35:  # '#'
                continue
            vis[base + j] = 0
            if c == 83:  # 'S'
                s = base + j
            elif c == 69:  # 'E'
                e = base + j
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    vis[s] = 1
    frontier = [s]
    steps = 0
    while frontier:
        steps += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            q = p - 1
            if not vis[q]:
                vis[q] = 1
                if q == e:
                    print(steps)
                    return
                app(q)
            q = p + 1
            if not vis[q]:
                vis[q] = 1
                if q == e:
                    print(steps)
                    return
                app(q)
            q = p - W
            if not vis[q]:
                vis[q] = 1
                if q == e:
                    print(steps)
                    return
                app(q)
            q = p + W
            if not vis[q]:
                vis[q] = 1
                if q == e:
                    print(steps)
                    return
                app(q)
        frontier = nxt
    print(-1)


main()
