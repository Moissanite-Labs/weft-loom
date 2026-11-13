import sys
def solve(lines):
    w=len(lines[0])+2
    flat=bytearray(b'#'*w)
    for l in lines: flat+=b'#'+l+b'#'
    flat+=b'#'*w
    s=flat.find(b'S'); e=flat.find(b'E')
    if s<0 or e<0: return -1
    blocked=flat
    blocked[e]=46
    t=bytes(1 if c==35 else 0 for c in range(256))
    b=bytearray(flat.translate(t)); b[s]=1
    fr=[s]; d=0
    while fr:
        d+=1; nx=[]
        for p in fr:
            for q in (p-w,p+w,p-1,p+1):
                if not b[q]:
                    if q==e: return d
                    b[q]=1; nx.append(q)
        fr=nx
    return -1
if __name__=="__main__":
    L=[l.strip() for l in sys.stdin.buffer.read().split(b'\n') if l.strip()]
    print(solve(L))
