import sys


def solve(rows):
    rows = [r for r in rows if r]
    if not rows:
        return -1
    W = max(len(r) for r in rows) + 2
    border = '#' * W
    flat = border + ''.join('#' + r.ljust(W - 2, '#') + '#' for r in rows) + border
    s = flat.find('S')
    e = flat.find('E')
    if s < 0 or e < 0:
        return -1
    if s == e:
        return 0
    t = flat.translate({ord('#'): 1, ord('.'): 0, ord('S'): 0, ord('E'): 0})
    seen = bytearray(t.encode('latin-1'))
    seen[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for i in frontier:
            for j in (i - 1, i + 1, i - W, i + W):
                if not seen[j]:
                    if j == e:
                        return d
                    seen[j] = 1
                    app(j)
        frontier = nxt
    return -1


def main():
    rows = sys.stdin.read().split()
    print(solve(rows))


if __name__ == "__main__":
    main()
