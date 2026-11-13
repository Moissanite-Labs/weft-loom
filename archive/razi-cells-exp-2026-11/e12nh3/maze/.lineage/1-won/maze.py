import sys
def solve(lines):
    w=len(lines[0]); W=w+2
    b='#'*W
    g=bytearray((b+''.join('#'+l+'#' for l in lines)+b).encode())
    s=g.find(b'S'); e=g.find(b'E')
    if s<0 or e<0: return -1
    g[s]=35
    cur=[s]; d=0
    while cur:
        d+=1
        nxt=[]
        ap=nxt.append
        for p in cur:
            for q in (p-1,p+1,p-W,p+W):
                if g[q]!=35:
                    if q==e: return d
                    g[q]=35; ap(q)
        cur=nxt
    return -1
if __name__=="__main__":
    L=[l for l in sys.stdin.read().split('\n') if l]
    print(solve(L))
