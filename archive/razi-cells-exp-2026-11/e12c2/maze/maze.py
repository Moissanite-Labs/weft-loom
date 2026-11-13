import sys
def main():
    lines = sys.stdin.read().split()
    h = len(lines); w = len(lines[0])
    s = ''.join(lines)
    W = w + 1
    # pad with wall column
    g = bytearray(('#'.join(lines) + '#').encode())
    st = g.find(b'S'); en = g.find(b'E')
    if st < 0 or en < 0:
        print(-1); return
    g[st] = 35
    fr = [st]; d = 0
    while fr:
        d += 1
        nf = []
        ap = nf.append
        for p in fr:
            for q in (p-1, p+1, p-W, p+W):
                if 0 <= q < len(g):
                    c = g[q]
                    if c == 46:
                        g[q] = 35; ap(q)
                    elif c == 69:
                        print(d); return
        fr = nf
    print(-1)
main()
