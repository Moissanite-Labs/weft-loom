import sys
def main():
    lines=sys.stdin.read().split()
    h=len(lines); w=len(lines[0])
    g=''.join(lines)
    s=g.find('S'); e=g.find('E')
    if s<0 or e<0: print(-1); return
    seen=bytearray(h*w)
    for i,c in enumerate(g):
        if c=='#': seen[i]=1
    seen[s]=1
    fr=[s]; d=0
    while fr:
        if seen[e] and e in fr: print(d); return
        nx=[]
        for p in fr:
            if p==e: print(d); return
            x=p%w
            if x>0 and not seen[p-1]: seen[p-1]=1; nx.append(p-1)
            if x<w-1 and not seen[p+1]: seen[p+1]=1; nx.append(p+1)
            if p>=w and not seen[p-w]: seen[p-w]=1; nx.append(p-w)
            if p+w<h*w and not seen[p+w]: seen[p+w]=1; nx.append(p+w)
        fr=nx; d+=1
    print(-1)
main()
