import sys
def solve(lines):
    h=len(lines); w=len(lines[0])
    W=w+1
    g=bytearray(('\n'.join(lines)+'\n').encode())
    s=g.index(b'S'); e=g.index(b'E')
    dist=0; fr=[s]; g[s]=35
    while fr:
        nf=[]
        for p in fr:
            if p==e: return dist
            for q in (p+1,p-1,p+W,p-W):
                if 0<=q<len(g) and g[q] in (46,69):
                    if q==e: return dist+1
                    g[q]=35; nf.append(q)
        fr=nf; dist+=1
    return -1
if __name__=="__main__":
    L=[l for l in sys.stdin.read().split('\n') if l]
    print(solve(L))
