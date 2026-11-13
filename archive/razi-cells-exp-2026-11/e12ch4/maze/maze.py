import sys
def solve(lines):
    h=len(lines); w=len(lines[0]) if h else 0
    s=e=-1
    g=bytearray(b''.join(l.encode() for l in lines))
    s=g.find(b'S'); e=g.find(b'E')
    if s<0 or e<0: return -1
    W=w
    dist={s:0}
    seen=bytearray(len(g))
    seen[s]=1
    fr=[s]; d=0
    while fr:
        d+=1
        nx=[]
        for p in fr:
            x=p%W
            for q,ok in ((p-W,p>=W),(p+W,p+W<len(g)),(p-1,x>0),(p+1,x<W-1)):
                if ok and not seen[q] and g[q]!=35:
                    if q==e: return d
                    seen[q]=1; nx.append(q)
        fr=nx
    return -1
if __name__=="__main__":
    L=[l.rstrip('\n') for l in sys.stdin if l.strip()]
    print(solve(L))
