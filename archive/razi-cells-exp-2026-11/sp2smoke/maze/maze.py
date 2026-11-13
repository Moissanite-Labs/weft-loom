import sys


def solve(rows):
    H = len(rows)
    if H == 0:
        return -1
    W = len(rows[0])
    flat = b"".join(rows)
    N = H * W
    s = flat.find(b"S")
    e = flat.find(b"E")
    if s < 0 or e < 0:
        return -1
    if s == e:
        return 0
    table = bytes(1 if i == 35 else 0 for i in range(256))
    vis = bytearray(flat.translate(table))
    vis[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for i in frontier:
            c = i % W
            if i >= W:
                j = i - W
                if not vis[j]:
                    if j == e:
                        return d
                    vis[j] = 1
                    app(j)
            if i + W < N:
                j = i + W
                if not vis[j]:
                    if j == e:
                        return d
                    vis[j] = 1
                    app(j)
            if c > 0:
                j = i - 1
                if not vis[j]:
                    if j == e:
                        return d
                    vis[j] = 1
                    app(j)
            if c < W - 1:
                j = i + 1
                if not vis[j]:
                    if j == e:
                        return d
                    vis[j] = 1
                    app(j)
        frontier = nxt
    return -1


def main():
    rows = [r for r in sys.stdin.buffer.read().split() if r]
    print(solve(rows))


if __name__ == "__main__":
    main()
