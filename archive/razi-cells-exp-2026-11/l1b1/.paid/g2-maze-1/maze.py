import sys
def main():
    lines = sys.stdin.buffer.read().split()
    W = max(map(len, lines)) + 2
    border = b"#" * W
    data = border + b"".join(b"#" + l.ljust(W - 2, b"#") + b"#" for l in lines) + border
    s = data.find(b"S")
    e = data.find(b"E")
    tb = bytearray(b"\x01" * 256)
    for c in b".SE":
        tb[c] = 0
    vis = bytearray(data.translate(bytes(tb)))
    vis[s] = 1
    frontier = [s]
    d = 0
    while frontier:
        d += 1
        nxt = []
        app = nxt.append
        for p in frontier:
            for q in (p + 1, p - 1, p + W, p - W):
                if not vis[q]:
                    if q == e:
                        print(d)
                        return
                    vis[q] = 1
                    app(q)
        frontier = nxt
    print(-1)
main()
