import sys
def solve(lines):
    w=max(len(l) for l in lines)
    W=w+1
    s=("".join(l.ljust(w,'#')+'#' for l in lines))
    si=s.index('S'); ei=s.index('E')
    # bit i = cell i
    t=s.replace('S','.').replace('E','.')
    op=int(t.translate({35:'0',46:'1'})[::-1],2)
    cur=1<<si; vis=cur; eb=1<<ei; d=0
    while cur:
        d+=1
        n=((cur<<1)|(cur>>1)|(cur<<W)|(cur>>W))&op&~vis
        if n&eb: return d
        vis|=n; cur=n
    return -1
if __name__=="__main__":
    print(solve(sys.stdin.read().split()))
