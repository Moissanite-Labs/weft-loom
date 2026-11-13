import sys
def main():
    lines=sys.stdin.read().split()
    h=len(lines);w=len(lines[0])
    W=w+2
    g=bytearray(b'\x01')*(W*(h+2))
    s=e=-1
    for i,l in enumerate(lines):
        b=(i+1)*W+1
        for j,c in enumerate(l):
            if c!='#':
                g[b+j]=0
                if c=='S':s=b+j
                elif c=='E':e=b+j
    g[s]=1
    fr=[s];d=0
    while fr:
        d+=1
        nf=[]
        a=nf.append
        for p in fr:
            for q in (p+1,p-1,p+W,p-W):
                if not g[q]:
                    if q==e:
                        print(d);return
                    g[q]=1;a(q)
        fr=nf
    print(-1)
main()
