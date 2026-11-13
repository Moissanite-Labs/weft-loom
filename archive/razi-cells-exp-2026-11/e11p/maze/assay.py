import random,time,sys
from collections import deque
from maze import solve
def gen(n,seed,p=0.28):
    r=random.Random(seed)
    g=[['#' if r.random()<p else '.' for _ in range(n)] for _ in range(n)]
    g[0][0]='S';g[n-1][n-1]='E'
    return [''.join(x) for x in g]
def ref(L):
    h=len(L);w=len(L[0])
    for i in range(h):
        for j in range(w):
            if L[i][j]=='S':s=(i,j)
    D={s:0};q=deque([s])
    while q:
        a,b=q.popleft()
        for x,y in((a+1,b),(a-1,b),(a,b+1),(a,b-1)):
            if 0<=x<h and 0<=y<w and L[x][y]!='#' and (x,y) not in D:
                D[(x,y)]=D[(a,b)]+1
                if L[x][y]=='E':return D[(x,y)]
                q.append((x,y))
    return -1
for sd in range(30):
    m=gen(12,sd,0.35)
    if solve(m)!=ref(m):print(0);sys.exit()
if solve(["S#E"])!=-1:print(0);sys.exit()
m=gen(2000,1)
t=time.time();r=solve(m);t=time.time()-t
print(1/t if r==ref(m) else 0)
