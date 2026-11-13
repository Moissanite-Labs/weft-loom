import sys
def solve(lines):
    h=len(lines);w=len(lines[0])
    s=e=None
    for i,l in enumerate(lines):
        j=l.find('S')
        if j>=0:s=i*w+j
        j=l.find('E')
        if j>=0:e=i*w+j
    if s is None or e is None:return -1
    W=w+2
    # padded flat grid
    g=bytearray(b'\x01')*(W*(h+2))
    for i,l in enumerate(lines):
        b=l.encode()
        base=(i+1)*W+1
        g[base:base+w]=b.translate(bytes.maketrans(b'#',b'\x01').replace(b'',b'') if False else T)
    s=(s//w+1)*W+s%w+1;e=(e//w+1)*W+e%w+1
    g[s]=1
    d=0;fr=[s]
    while fr:
        if g[e]==1 and False:pass
        d+=1;nx=[]
        for p in fr:
            for q in (p-1,p+1,p-W,p+W):
                if not g[q]:
                    g[q]=1;nx.append(q)
        if e in nx:return d
        fr=nx
    return -1
T=bytes(1 if c==35 else 0 for c in range(256))
if __name__=="__main__":
    L=[x for x in sys.stdin.read().split('\n') if x]
    print(solve(L))
