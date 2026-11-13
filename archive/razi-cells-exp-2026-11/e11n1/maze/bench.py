import random,time,sys
from collections import deque
import maze
def gen(n,seed):
    r=random.Random(seed)
    g=[['#' if r.random()<0.25 else '.' for _ in range(n)] for _ in range(n)]
    g[0][0]='S';g[n-1][n-1]='E'
    return [''.join(x) for x in g]
def ref(L):
    h=len(L);w=len(L[0])
    for i in range(h):
        for j in range(w):
            if L[i][j]=='S':s=(i,j)
            if L[i][j]=='E':e=(i,j)
    D={s:0};q=deque([s])
    while q:
        i,j=q.popleft()
        if (i,j)==e:return D[e]
        for a,b in((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
            if 0<=a<h and 0<=b<w and L[a][b]!='#' and (a,b) not in D:
                D[(a,b)]=D[(i,j)]+1;q.append((a,b))
    return -1
for n,sd in((30,1),(30,2),(50,3),(40,4),(60,5)):
    L=gen(n,sd)
    if maze.solve(L)!=ref(L):print(0);sys.exit()
L=gen(2000,7)
t=time.time();r=maze.solve(L);t=time.time()-t
print(1/t if r!=-2 else 0)
