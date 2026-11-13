import sys


def main():
    rows = sys.stdin.buffer.read().split()
    if not rows:
        print(-1)
        return
    H = len(rows)
    W = max(len(r) for r in rows)
    W2 = W + 2
    # padded grid: border of '#' so neighbours never go out of bounds
    pad = bytearray(b'#' * (W2 * (H + 2)))
    for i, r in enumerate(rows):
        base = (i + 1) * W2 + 1
        pad[base:base + len(r)] = r
    s = pad.find(b'S')
    e = pad.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    if s == e:
        print(0)
        return
    # open cells: 1 if not '#', else 0 (bytes translate table)
    table = bytearray(256)
    for c in range(256):
        table[c] = 0 if c == 35 else 1  # '#'
    opn = bytes(pad).translate(bytes(table))
    vis = bytearray(len(pad))
    vis[s] = 1
    frontier = [s]
    steps = 0
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            if p == e:
                print(steps)
                return
            for q in (p - 1, p + 1, p - W2, p + W2):
                if opn[q] and not vis[q]:
                    vis[q] = 1
                    app(q)
        frontier = nxt
        steps += 1
    print(-1)


main()
