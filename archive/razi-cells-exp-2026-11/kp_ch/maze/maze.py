import sys
def main():
    lines=sys.stdin.read().split()
    h=len(lines);w=len(lines[0])
    W=w+2
    g=bytearray(b'#'*(W*(h+2)))
    for i,l in enumerate(lines):
        g[(i+1)*W+1:(i+1)*W+1+w]=l.encode()
    S=g.index(b'S');E=g.index(b'E')
    g[S]=35
    g[E]=69
    fr=[S];d=0
    while fr:
        d+=1;nx=[];a=nx.append
        for p in fr:
            q=p+1
            if g[q]!=35:
                g[q]=35;a(q)
            q=p-1
            if g[q]!=35:
                g[q]=35;a(q)
            q=p+W
            if g[q]!=35:
                g[q]=35;a(q)
            q=p-W
            if g[q]!=35:
                g[q]=35;a(q)
        if E in nx:
            print(d);return
        fr=nx
    print(-1)
main()
