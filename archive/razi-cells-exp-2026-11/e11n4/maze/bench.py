import random,time
from collections import deque
from maze import solve
def gen(n,seed,p=0.28):
    r=random.Random(seed)
    g=[['#' if r.random()<p else '.' for _ in range(n)] for _ in range(n)]
    g[0][0]='S'; g[n-1][n-1]='E'
    return [''.join(x) for x in g]
def ref(L):
    h=len(L);w=len(L[0])
    for i in range(h):
        for j in range(w):
            if L[i][j]=='S':s=(i,j)
            if L[i][j]=='E':e=(i,j)
    D={s:0};q=deque([s])
    while q:
        a,b=q.popleft()
        if (a,b)==e:return D[e]
        for x,y in((a+1,b),(a-1,b),(a,b+1),(a,b-1)):
            if 0<=x<h and 0<=y<w and L[x][y]!='#' and (x,y) not in D:
                D[(x,y)]=D[(a,b)]+1;q.append((x,y))
    return -1
for sd in range(30):
    L=gen(12,sd,0.35)
    if solve(L)!=ref(L):print(0);raise SystemExit
L=gen(2000,1)
t=time.time();r=solve(L);t=time.time()-t
print(round(1/t,3) if r==ref(L) else 0)
