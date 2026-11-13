import sys


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        print(-1)
        return
    W = len(data[0])
    W2 = W + 2
    buf = b'#' * W2 + b''.join(b'#' + r[:W] + b'#' for r in data) + b'#' * W2
    s = buf.find(b'S')
    e = buf.find(b'E')
    if s < 0 or e < 0:
        print(-1)
        return
    tbl = bytes(1 if c == 35 else 0 for c in range(256))
    vis = bytearray(buf.translate(tbl))
    vis[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        for i in frontier:
            for j in (i - 1, i + 1, i - W2, i + W2):
                if not vis[j]:
                    if j == e:
                        print(d)
                        return
                    vis[j] = 1
                    nxt.append(j)
        frontier = nxt
    print(-1)


main()
