import sys
from collections import deque
rows=[r for r in sys.stdin.read().split() if r]
h=len(rows);w=len(rows[0])
for i in range(h):
    for j in range(w):
        if rows[i][j]=='S': s=(i,j)
        if rows[i][j]=='E': e=(i,j)
dist={s:0};q=deque([s])
while q:
    i,j=q.popleft()
    if (i,j)==e: print(dist[(i,j)]); sys.exit()
    for a,b in ((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
        if 0<=a<h and 0<=b<w and rows[a][b]!='#' and (a,b) not in dist:
            dist[(a,b)]=dist[(i,j)]+1; q.append((a,b))
print(-1)
