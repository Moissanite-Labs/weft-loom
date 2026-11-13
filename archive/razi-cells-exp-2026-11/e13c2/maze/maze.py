import sys
def main():
    lines=sys.stdin.read().split()
    h=len(lines);w=len(lines[0])
    W=w+2
    g=bytearray(b'#'*(W*(h+2)))
    for i,l in enumerate(lines):
        g[(i+1)*W+1:(i+1)*W+1+w]=l.encode()
    s=g.find(b'S');e=g.find(b'E')
    if s<0 or e<0:
        print(-1);return
    g[s]=35
    fr=[s];d=0
    d4=(1,-1,W,-W)
    while fr:
        d+=1
        nx=[]
        for p in fr:
            for k in d4:
                q=p+k
                c=g[q]
                if c!=35:
                    if q==e:
                        print(d);return
                    g[q]=35
                    nx.append(q)
        fr=nx
    print(-1)
main()
