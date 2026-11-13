import sys
def solve(lines):
    h=len(lines); w=len(lines[0])
    W=w+2
    g=bytearray(b'#'*(W*(h+2)))
    for i,l in enumerate(lines):
        g[(i+1)*W+1:(i+1)*W+1+w]=l.encode()
    s=g.index(b'S'); e=g.index(b'E')
    dist={s:0}
    d=bytearray(len(g))
    d[s]=1
    cur=[s];n=0
    while cur:
        n+=1;nxt=[]
        for p in cur:
            for q in (p-1,p+1,p-W,p+W):
                if g[q]!=35 and not d[q]:
                    if q==e: return n
                    d[q]=1;nxt.append(q)
        cur=nxt
    return -1
if __name__=="__main__":
    print(solve(sys.stdin.read().split()))
