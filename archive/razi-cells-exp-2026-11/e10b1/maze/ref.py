import sys
from collections import deque
g = sys.stdin.read().split('\n')
g = [r for r in g if r]
for i,r in enumerate(g):
    if 'S' in r: s=(i,r.index('S'))
    if 'E' in r: e=(i,r.index('E'))
d={s:0}; q=deque([s]); ans=-1
while q:
    c=q.popleft()
    if c==e: ans=d[c]; break
    for di,dj in((1,0),(-1,0),(0,1),(0,-1)):
        a,b=c[0]+di,c[1]+dj
        if 0<=a<len(g) and 0<=b<len(g[a]) and g[a][b]!='#' and (a,b) not in d:
            d[(a,b)]=d[c]+1; q.append((a,b))
print(ans)
