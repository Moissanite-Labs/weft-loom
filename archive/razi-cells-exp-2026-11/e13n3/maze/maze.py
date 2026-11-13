import sys
def main():
    L=[l for l in sys.stdin.read().split('\n') if l.strip()]
    h=len(L);w=len(L[0].rstrip())
    W=w+2
    g=bytearray(b'\x01'*(W*(h+2)))
    s=e=-1
    for i,l in enumerate(L):
        b=i*W+W+1
        for j,c in enumerate(l[:w]):
            if c!='#':
                g[b+j]=0
                if c=='S':s=b+j
                elif c=='E':e=b+j
    if s<0 or e<0:print(-1);return
    g[s]=1
    fr=[s];d=0
    while fr:
        d+=1
        n=[]
        a=n.append
        for p in fr:
            for q in (p-1,p+1,p-W,p+W):
                if not g[q]:
                    if q==e:print(d);return
                    g[q]=1;a(q)
        fr=n
    print(-1)
main()
