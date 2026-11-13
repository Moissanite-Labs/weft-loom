import sys
def solve(lines):
    w=len(lines[0])+2
    pad=b'#'*w
    s=pad+b''.join(b'#'+l+b'#' for l in lines)+pad
    a=s.find(b'S'); e=s.find(b'E')
    if a<0 or e<0: return -1
    seen=bytearray(s.translate(bytes.maketrans(b'#',b'\x01').replace(b'',b'') if False else bytes(1 if i==35 else 0 for i in range(256))))
    seen[a]=1
    fr=[a]; d=0
    st=(-w,w,-1,1)
    while fr:
        d+=1; nx=[]
        for p in fr:
            for o in st:
                q=p+o
                if not seen[q]:
                    if q==e: return d
                    seen[q]=1
                    nx.append(q)
        fr=nx
    return -1
if __name__=="__main__":
    L=[l.rstrip() for l in sys.stdin.buffer.read().split(b'\n') if l.strip()]
    print(solve(L))
