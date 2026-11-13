import sys
from collections import deque
g=[l for l in sys.stdin.read().split('\n') if l]
H=len(g);W=len(g[0])
for i in range(H):
    for j in range(W):
        if g[i][j]=='S':s=(i,j)
        if g[i][j]=='E':e=(i,j)
D=[[-1]*W for _ in range(H)];D[s[0]][s[1]]=0;q=deque([s])
while q:
    i,j=q.popleft()
    for a,b in((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
        if 0<=a<H and 0<=b<W and D[a][b]<0 and g[a][b]!='#':
            D[a][b]=D[i][j]+1;q.append((a,b))
print(D[e[0]][e[1]])
