import sys
def main():
    L=sys.stdin.buffer.read().split()
    h=len(L);w=len(L[0])
    W=w+2
    g=bytearray(b'#'*(W*(h+2)))
    for i,r in enumerate(L):
        g[(i+1)*W+1:(i+1)*W+1+w]=r
    s=g.index(b'S');e=g.index(b'E')
    g[s]=35
    f=[s];d=0
    while f:
        d+=1
        n=[]
        a=n.append
        for p in f:
            q=p-1
            if g[q]!=35:
                g[q]=35;a(q)
            q=p+1
            if g[q]!=35:
                g[q]=35;a(q)
            q=p-W
            if g[q]!=35:
                g[q]=35;a(q)
            q=p+W
            if g[q]!=35:
                g[q]=35;a(q)
        if g[e]==35:
            print(d);return
        f=n
    print(-1)
main()
