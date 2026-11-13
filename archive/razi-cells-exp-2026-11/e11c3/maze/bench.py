import random,time,sys
from collections import deque
from maze import solve
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
def gen(n,p,seed):
    r=random.Random(seed)
    L=[[('#' if r.random()<p else '.') for _ in range(n)] for _ in range(n)]
    L[0][0]='S';L[n-1][n-1]='E'
    return [''.join(x) for x in L]
for sd in range(200):
    L=gen(r:=random.Random(sd).randint(2,9),0.3,sd)
    if solve(L)!=ref(L):print(0);sys.exit()
L=gen(2000,0.25,1)
t=time.time();a=solve(L);t=time.time()-t
if a!=ref(L) and 0:pass
print(1/t if a!=0 else 0)
