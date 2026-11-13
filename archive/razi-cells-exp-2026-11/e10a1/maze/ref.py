import sys
from collections import deque
rows = sys.stdin.read().split('\n')
rows = [r for r in rows if r]
dist = {}
for i,r in enumerate(rows):
    for j,ch in enumerate(r):
        if ch=='S': s=(i,j)
        if ch=='E': e=(i,j)
dist[s]=0; q=deque([s]); ans=-1
while q:
    i,j=q.popleft()
    if (i,j)==e: ans=dist[(i,j)]; break
    for a,b in ((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
        if 0<=a<len(rows) and 0<=b<len(rows[a]) and rows[a][b]!='#' and (a,b) not in dist:
            dist[(a,b)]=dist[(i,j)]+1; q.append((a,b))
print(ans)
