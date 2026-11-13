import sys
from collections import deque
g=sys.stdin.read().split()
h=len(g);w=len(g[0])
for i in range(h):
    for j in range(w):
        if g[i][j]=='S':s=(i,j)
        if g[i][j]=='E':e=(i,j)
D={s:0};q=deque([s])
while q:
    i,j=q.popleft()
    if (i,j)==e:print(D[(i,j)]);sys.exit()
    for a,b in((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
        if 0<=a<h and 0<=b<w and g[a][b]!='#' and (a,b) not in D:
            D[(a,b)]=D[(i,j)]+1;q.append((a,b))
print(-1)
