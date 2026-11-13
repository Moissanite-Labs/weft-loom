import sys
from heapq import heappush, heappop
from array import array

def solve():
    rows=sys.stdin.buffer.read().splitlines()
    if not rows:
        print(-1); return
    stride=len(rows[0])+2
    grid=bytearray(b'#'*stride+b''.join(b'#'+r+b'#' for r in rows)+b'#'*stride)
    start=grid.find(b'S'); end=grid.find(b'E')
    if start<0 or end<0:
        print(-1); return
    er,ec=divmod(end,stride)
    sr,sc=divmod(start,stride)
    best=array('i',[-1])*len(grid); best[start]=0
    heap=[(abs(sr-er)+abs(sc-ec),0,start)]
    while heap:
        f,neg,p=heappop(heap)
        d=-neg
        if best[p]!=d or grid[p]==35: continue
        if p==end:
            print(d); return
        grid[p]=35
        nd=d+1
        for q in (p-1,p+1,p-stride,p+stride):
            if grid[q]!=35 and (best[q]<0 or nd<best[q]):
                best[q]=nd
                r,c=divmod(q,stride)
                heappush(heap,(nd+abs(r-er)+abs(c-ec),-nd,q))
    print(-1)

if __name__=='__main__': solve()
