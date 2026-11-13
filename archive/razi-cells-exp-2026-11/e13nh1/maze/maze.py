import sys
def main():
    L=sys.stdin.read().split()
    h=len(L);w=len(L[0]);W=w+2
    g=bytearray(b'#'*(W*(h+2)))
    for i,r in enumerate(L):
        g[(i+1)*W+1:(i+1)*W+1+w]=r.encode()
    s=g.index(b'S');e=g.index(b'E')
    g[s]=35
    fr=[s];d=0
    st=(1,-1,W,-W)
    while fr:
        d+=1;nf=[]
        for p in fr:
            for t in st:
                q=p+t
                if g[q]!=35:
                    if q==e:
                        print(d);return
                    g[q]=35;nf.append(q)
        fr=nf
    print(-1)
main()
