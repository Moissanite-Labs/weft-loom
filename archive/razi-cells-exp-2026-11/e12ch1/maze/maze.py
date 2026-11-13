import sys
def main():
    lines=sys.stdin.buffer.read().split()
    h=len(lines); w=len(lines[0]) if h else 0
    g=b''.join(lines)
    s=g.find(b'S'); e=g.find(b'E')
    if s<0 or e<0: print(-1); return
    n=h*w
    seen=bytearray(g.translate(bytes.maketrans(b'#',b'\x01').replace(b'',b'')) ) if False else bytearray(1 if c==35 else 0 for c in g) if n<0 else bytearray(g.replace(b'.',b'\x00').replace(b'S',b'\x00').replace(b'E',b'\x00').replace(b'#',b'\x01'))
    seen[s]=1
    fr=[s]; d=0
    while fr:
        nx=[]
        for p in fr:
            if p==e: print(d); return
            x=p%w
            if x>0 and not seen[p-1]: seen[p-1]=1; nx.append(p-1)
            if x<w-1 and not seen[p+1]: seen[p+1]=1; nx.append(p+1)
            if p>=w and not seen[p-w]: seen[p-w]=1; nx.append(p-w)
            if p+w<n and not seen[p+w]: seen[p+w]=1; nx.append(p+w)
        fr=nx; d+=1
    print(-1)
main()
