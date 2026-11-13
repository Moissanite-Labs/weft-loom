import sys

TBL = bytes(1 if c == 35 else 0 for c in range(256))


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        print(-1)
        return
    W = max(len(r) for r in data) + 2
    rows = [b'#' * W]
    for r in data:
        rows.append(b'#' + r.ljust(W - 2, b'#') + b'#')
    rows.append(b'#' * W)
    grid = b''.join(rows)
    s = grid.find(b'S')
    e = grid.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    seen = bytearray(grid.translate(TBL))
    seen[s] = 1
    cur = [s]
    d = 0
    while cur:
        d += 1
        nxt = []
        app = nxt.append
        for i in cur:
            for j in (i - W, i + W, i - 1, i + 1):
                if not seen[j]:
                    if j == e:
                        print(d)
                        return
                    seen[j] = 1
                    app(j)
        cur = nxt
    print(-1)


if __name__ == '__main__':
    main()
