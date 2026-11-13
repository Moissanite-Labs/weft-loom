import sys
def solve(lines):
    h=len(lines); w=len(lines[0])
    W=w+1
    g=bytearray(("".join(l.ljust(w,'#')+'#' for l in lines)).encode())
    s=g.find(b'S'); e=g.find(b'E')
    if s<0 or e<0: return -1
    g[s]=35
    cur=[s]; d=0
    while cur:
        d+=1; nxt=[]
        for p in cur:
            for q in (p+1,p-1,p+W,p-W):
                if 0<=q<len(g) and g[q]!=35:
                    if q==e: return d
                    g[q]=35; nxt.append(q)
        cur=nxt
    return -1
if __name__=="__main__":
    print(solve(sys.stdin.read().split()))
