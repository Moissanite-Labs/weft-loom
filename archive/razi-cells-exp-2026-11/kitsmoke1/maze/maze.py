import sys
def main():
    data=sys.stdin.buffer.read().split()
    w=len(data[0]);W=w+2
    pad=b'#'*W
    t=bytearray(pad+b''.join(b'#'+r+b'#' for r in data)+pad)
    s=t.index(b'S');e=t.index(b'E')
    t[s]=35
    g=t.translate(bytes([0 if c!=35 else 1 for c in range(256)]))
    g=bytearray(g)
    g[s]=1
    fr=[s];d=0
    while fr:
        d+=1
        n=[]
        a=n.append
        for p in fr:
            q=p-1
            if not g[q]:
                if q==e:print(d);return
                g[q]=1;a(q)
            q=p+1
            if not g[q]:
                if q==e:print(d);return
                g[q]=1;a(q)
            q=p-W
            if not g[q]:
                if q==e:print(d);return
                g[q]=1;a(q)
            q=p+W
            if not g[q]:
                if q==e:print(d);return
                g[q]=1;a(q)
        fr=n
    print(-1)
main()
