import sys


def main():
    rows = [r for r in sys.stdin.read().split() if r]
    if not rows:
        print(-1)
        return
    W = max(len(r) for r in rows)
    rows = ['#' * (W + 2)] + ['#' + r.ljust(W, '#') + '#' for r in rows] + ['#' * (W + 2)]
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
    # mark: 0 open, 1 wall, 2 reached from S, 3 reached from E
    tbl = bytes(1 if i == 35 else 0 for i in range(256))
    mark = bytearray(flat.encode().translate(tbl))
    mark[s] = 2
    mark[e] = 3
    FA = [s]
    FB = [e]
    dA = 0
    dB = 0
    while FA and FB:
        if len(FA) <= len(FB):
            nxt = []
            app = nxt.append
            for p in FA:
                for q in (p - 1, p + 1, p - W2, p + W2):
                    m = mark[q]
                    if m == 3:
                        print(dA + 1 + dB)
                        return
                    if m == 0:
                        mark[q] = 2
                        app(q)
            FA = nxt
            dA += 1
        else:
            nxt = []
            app = nxt.append
            for p in FB:
                for q in (p - 1, p + 1, p - W2, p + W2):
                    m = mark[q]
                    if m == 2:
                        print(dA + dB + 1)
                        return
                    if m == 0:
                        mark[q] = 3
                        app(q)
            FB = nxt
            dB += 1
    print(-1)


main()
