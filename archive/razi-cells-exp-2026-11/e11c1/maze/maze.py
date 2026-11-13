import sys
def solve(lines):
    h=len(lines); w=len(lines[0])
    s=''.join(lines)
    a=s.find('S'); e=s.find('E')
    if a<0 or e<0: return -1
    blocked=bytearray(1 if c=='#' else 0 for c in s)
    dist=[-1]*len(s); dist[a]=0
    fr=[a]; d=0
    while fr:
        d+=1; nf=[]
        for p in fr:
            x=p%w
            for q,ok in ((p-w,p>=w),(p+w,p<len(s)-w),(p-1,x>0),(p+1,x<w-1)):
                if ok and not blocked[q] and dist[q]<0:
                    dist[q]=d; nf.append(q)
        if dist[e]>=0: return dist[e]
        fr=nf
    return -1
if __name__=="__main__":
    L=[l.rstrip('\n') for l in sys.stdin if l.strip()]
    print(solve(L))
