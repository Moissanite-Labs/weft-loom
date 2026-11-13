import sys
def solve(lines):
    h=len(lines); w=len(lines[0])
    W=w+1
    g=bytearray(("".join(l.ljust(w,'#')+'#' for l in lines)).encode())
    s=g.find(b'S'); e=g.find(b'E')
    if s<0 or e<0: return -1
    dist=0; fr=[s]; g[s]=35
    while fr:
        nf=[]
        dist+=1
        for p in fr:
            for q in (p-1,p+1,p-W,p+W):
                if 0<=q<len(g):
                    c=g[q]
                    if c!=35:
                        if q==e: return dist
                        g[q]=35; nf.append(q)
        fr=nf
    return -1
if __name__=="__main__":
    print(solve(sys.stdin.read().split()))
