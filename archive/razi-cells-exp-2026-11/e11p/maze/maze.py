import sys
def solve(lines):
    h=len(lines); w=len(lines[0])
    W=w+2
    g=bytearray(b'#'*(W*(h+2)))
    s=e=-1
    for i,l in enumerate(lines):
        b=l.encode()
        o=(i+1)*W+1
        g[o:o+w]=b
        j=b.find(b'S')
        if j>=0:s=o+j
        j=b.find(b'E')
        if j>=0:e=o+j
    if s<0 or e<0:return -1
    g[s]=35
    fr=[s];d=0
    ds=(1,-1,W,-W)
    while fr:
        d+=1;nx=[]
        for p in fr:
            for k in ds:
                q=p+k
                if g[q]!=35:
                    if q==e:return d
                    g[q]=35;nx.append(q)
        fr=nx
    return -1
if __name__=="__main__":
    print(solve([l for l in sys.stdin.read().split('\n') if l]))
