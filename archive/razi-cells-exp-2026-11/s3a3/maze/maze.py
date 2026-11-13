import sys


def solve(text):
    rows = [r.rstrip('\r') for r in text.split('\n') if r.strip() != '']
    if not rows:
        return -1
    W = max(len(r) for r in rows) + 2
    g = ('#' * W + ''.join('#' + r.ljust(W - 2, '#') + '#' for r in rows) + '#' * W).encode()
    s = g.find(b'S')
    e = g.find(b'E')
    if s < 0 or e < 0:
        return -1
    table = bytes(0 if i == 35 else 1 for i in range(256))
    free = bytearray(g.translate(table))
    free[s] = 0
    cur = [s]
    d = 0
    while cur:
        nxt = []
        app = nxt.append
        for p in cur:
            if p == e:
                return d
            for q in (p - 1, p + 1, p - W, p + W):
                if free[q]:
                    free[q] = 0
                    app(q)
        cur = nxt
        d += 1
    return -1


def main():
    print(solve(sys.stdin.read()))


if __name__ == '__main__':
    main()
