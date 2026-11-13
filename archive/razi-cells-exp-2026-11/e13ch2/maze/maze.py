import sys
def main():
    lines=sys.stdin.read().split()
    h=len(lines);w=len(lines[0]);W=w+2
    g=bytearray(b'#'*(W*(h+2)))
    for i,l in enumerate(lines):
        g[(i+1)*W+1:(i+1)*W+1+w]=l.encode()
    s=g.index(b'S');e=g.index(b'E')
    g[s]=35
    g[e]=69
    fr=[s];d=0
    while fr:
        d+=1;nf=[];a=nf.append
        for p in fr:
            q=p-1
            if g[q]!=35:
                if q==e:
                    print(d);return
                g[q]=35;a(q)
            q=p+1
            if g[q]!=35:
                if q==e:
                    print(d);return
                g[q]=35;a(q)
            q=p-W
            if g[q]!=35:
                if q==e:
                    print(d);return
                g[q]=35;a(q)
            q=p+W
            if g[q]!=35:
                if q==e:
                    print(d);return
                g[q]=35;a(q)
        fr=nf
    print(-1)
main()
