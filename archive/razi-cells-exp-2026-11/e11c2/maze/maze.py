import sys
def solve(lines):
    h=len(lines); w=len(lines[0])
    s="".join(lines)
    a=s.find('S'); e=s.find('E')
    if a<0 or e<0: return -1
    n=h*w
    b=bytearray(c=='#' for c in s.encode().decode())
    b[a]=1
    fr=[a]; d=0
    while fr:
        d+=1; nx=[]
        for p in fr:
            x=p%w
            if x and not b[p-1]: b[p-1]=1; nx.append(p-1)
            if x<w-1 and not b[p+1]: b[p+1]=1; nx.append(p+1)
            if p>=w and not b[p-w]: b[p-w]=1; nx.append(p-w)
            if p+w<n and not b[p+w]: b[p+w]=1; nx.append(p+w)
        if not b[e] or True:
            if e in nx: return d
        fr=nx
    return -1
if __name__=="__main__":
    L=[l.rstrip("\n") for l in sys.stdin if l.strip()]
    print(solve(L))
