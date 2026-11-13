import sys


def main():
    lines = sys.stdin.read().split()
    if not lines:
        print(-1)
        return
    W = max(len(l) for l in lines)
    border = '#' * (W + 2)
    rows = [border] + ['#' + l.ljust(W, '#') + '#' for l in lines] + [border]
    W2 = W + 2
    flat = ''.join(rows)
    s = flat.find('S')
    e = flat.find('E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    table = bytes.maketrans(b'#.SE', b'\x01\x00\x00\x00')
    vis = bytearray(flat.encode().translate(table))
    vis[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p - 1, p + 1, p - W2, p + W2):
                if not vis[q]:
                    if q == e:
                        print(d)
                        return
                    vis[q] = 1
                    app(q)
        frontier = nxt
    print(-1)


if __name__ == '__main__':
    main()
