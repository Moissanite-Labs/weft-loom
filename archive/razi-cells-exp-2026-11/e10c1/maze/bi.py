import sys
TR = bytes.maketrans(b'#\n.SE', b'\x00\x00\x01\x01\x01')
def main():
    data = sys.stdin.buffer.read()
    data = data.replace(b'\r', b'')
    nl = data.find(b'\n')
    if nl < 0:
        data += b'\n'; nl = len(data) - 1
    if not data.endswith(b'\n'):
        data += b'\n'
    W = nl + 1
    s = data.find(b'S'); e = data.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    g = bytearray(W) + data.translate(TR) + bytearray(W)
    s += W; e += W
    if s == e:
        print(0); return
    g[s] = 0
    g[e] = 2
    fa = [s]; fb = [e]
    da = 0; db = 0
    while fa and fb:
        if len(fa) <= len(fb):
            nxt = []
            app = nxt.append
            for p in fa:
                q = p - W
                v = g[q]
                if v:
                    if v == 1:
                        g[q] = 0; app(q)
                    else:
                        print(da + 1 + db); return
                q = p + W
                v = g[q]
                if v:
                    if v == 1:
                        g[q] = 0; app(q)
                    else:
                        print(da + 1 + db); return
                q = p - 1
                v = g[q]
                if v:
                    if v == 1:
                        g[q] = 0; app(q)
                    else:
                        print(da + 1 + db); return
                q = p + 1
                v = g[q]
                if v:
                    if v == 1:
                        g[q] = 0; app(q)
                    else:
                        print(da + 1 + db); return
            da += 1
            fa = nxt
        else:
            nxt = []
            app = nxt.append
            for p in fb:
                q = p - W
                v = g[q]
                if v == 1:
                    g[q] = 2; app(q)
                elif not v:
                    print(da + 1 + db); return
                q = p + W
                v = g[q]
                if v == 1:
                    g[q] = 2; app(q)
                elif not v:
                    print(da + 1 + db); return
                q = p - 1
                v = g[q]
                if v == 1:
                    g[q] = 2; app(q)
                elif not v:
                    print(da + 1 + db); return
                q = p + 1
                v = g[q]
                if v == 1:
                    g[q] = 2; app(q)
                elif not v:
                    print(da + 1 + db); return
            db += 1
            fb = nxt
    print(-1)
main()
