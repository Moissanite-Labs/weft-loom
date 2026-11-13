import sys
def main():
    data = sys.stdin.buffer.read().replace(b'\r', b'')
    lines = [l for l in data.split(b'\n') if l]
    if not lines:
        print(-1); return
    W = max(len(l) for l in lines) + 2
    buf = bytearray(b'#' * W)
    for l in lines:
        buf += b'#' + l.ljust(W - 2, b'#') + b'#'
    buf += b'#' * W
    s = buf.find(b'S')
    if s < 0 or buf.find(b'E') < 0:
        print(-1); return
    buf[s] = 35
    frontier = [s]
    d = 0
    while frontier:
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p - 1, p + 1, p - W, p + W):
                c = buf[q]
                if c != 35:
                    if c == 69:
                        print(d + 1); return
                    buf[q] = 35
                    app(q)
        frontier = nxt
        d += 1
    print(-1)
main()
