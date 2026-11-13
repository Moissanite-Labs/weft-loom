import sys
def solve(lines):
    h=len(lines); w=len(lines[0])
    s=''.join(lines)
    W=w
    a=s.find('S'); e=s.find('E')
    if a<0 or e<0: return -1
    blocked=bytearray(c=='#' for c in s)
    dist=[-1]*len(s)
    dist[a]=0
    fr=[a]; d=0
    while fr:
        d+=1; nx=[]
        for p in fr:
            x=p%W
            for q,ok in ((p-W,p>=W),(p+W,p+W<len(s)),(p-1,x>0),(p+1,x<W-1)):
                if ok and not blocked[q] and dist[q]<0:
                    dist[q]=d; nx.append(q)
            if dist[e]>=0: return dist[e]
        fr=nx
    return -1
if __name__=="__main__":
    L=[l for l in sys.stdin.read().split('\n') if l]
    print(solve(L))
