import sys
from collections import deque
g=[l.rstrip('\n') for l in sys.stdin if l.strip()]
H=len(g);W=len(g[0])
for r in range(H):
    for c in range(W):
        if g[r][c]=='S': s=(r,c)
        if g[r][c]=='E': e=(r,c)
D={s:0};q=deque([s])
while q:
    r,c=q.popleft()
    if (r,c)==e: print(D[(r,c)]); sys.exit()
    for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
        nr,nc=r+dr,c+dc
        if 0<=nr<H and 0<=nc<W and g[nr][nc]!='#' and (nr,nc) not in D:
            D[(nr,nc)]=D[(r,c)]+1;q.append((nr,nc))
print(-1)
