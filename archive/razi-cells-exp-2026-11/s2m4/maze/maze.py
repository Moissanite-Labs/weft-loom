import sys


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        print(-1)
        return
    W = len(data[0])
    P = W + 2
    pad = b'#' * P
    grid = pad + b''.join(b'#' + r + b'#' for r in data) + pad
    s = grid.find(b'S')
    e = grid.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    tbl = bytes(1 if i == 35 else 0 for i in range(256))
    seen = bytearray(grid.translate(tbl))
    seen[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for i in frontier:
            c = i - P
            if not seen[c]:
                if c == e:
                    print(d)
                    return
                seen[c] = 1
                app(c)
            c = i + P
            if not seen[c]:
                if c == e:
                    print(d)
                    return
                seen[c] = 1
                app(c)
            c = i - 1
            if not seen[c]:
                if c == e:
                    print(d)
                    return
                seen[c] = 1
                app(c)
            c = i + 1
            if not seen[c]:
                if c == e:
                    print(d)
                    return
                seen[c] = 1
                app(c)
        frontier = nxt
    print(-1)


main()
