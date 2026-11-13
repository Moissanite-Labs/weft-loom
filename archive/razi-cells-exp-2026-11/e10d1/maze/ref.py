import sys
from collections import deque
g=[l for l in sys.stdin.read().split('\n') if l]
H=len(g);W=len(g[0])
for i in range(H):
    for j in range(W):
        if g[i][j]=='S':s=(i,j)
        if g[i][j]=='E':e=(i,j)
dist={s:0};q=deque([s])
while q:
    i,j=q.popleft()
    if (i,j)==e:print(dist[(i,j)]);sys.exit()
    for a,b in((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
        if 0<=a<H and 0<=b<W and g[a][b]!='#' and (a,b) not in dist:
            dist[(a,b)]=dist[(i,j)]+1;q.append((a,b))
print(-1)
