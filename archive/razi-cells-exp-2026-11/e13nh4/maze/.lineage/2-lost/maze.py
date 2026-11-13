import sys
def main():
    lines=sys.stdin.read().split()
    h=len(lines);w=len(lines[0]) if h else 0
    W=w+2
    g=bytearray(b'#'*(W*(h+2)))
    for i,l in enumerate(lines):
        g[(i+1)*W+1:(i+1)*W+1+w]=l.encode()
    s=g.find(b'S');e=g.find(b'E')
    g[s]=35
    cur=[s];d=0
    dirs=(1,-1,W,-W)
    while cur:
        d+=1
        nxt=[]
        ap=nxt.append
        for p in cur:
            for k in dirs:
                q=p+k
                c=g[q]
                if c!=35:
                    if q==e:
                        print(d);return
                    g[q]=35;ap(q)
        cur=nxt
    print(-1)
main()
