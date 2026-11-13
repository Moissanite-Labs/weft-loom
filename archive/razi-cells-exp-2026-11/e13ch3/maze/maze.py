import sys
def main():
    lines=sys.stdin.read().split()
    h=len(lines);w=len(lines[0])
    W=w+2
    g=bytearray(b'#')*(W*(h+2))
    s=e=0
    for i,l in enumerate(lines):
        b=(i+1)*W+1
        g[b:b+w]=l.encode()
        j=l.find('S')
        if j>=0:s=b+j
        j=l.find('E')
        if j>=0:e=b+j
    g[s]=35
    fr=[s];d=0
    dirs=(1,-1,W,-W)
    while fr:
        d+=1
        nf=[]
        for p in fr:
            for k in dirs:
                q=p+k
                if g[q]!=35:
                    if q==e:
                        print(d);return
                    g[q]=35
                    nf.append(q)
        fr=nf
    print(-1)
main()
