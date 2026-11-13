import random,collections
from maze import solve
for t in range(300):
    r=random.Random(t);h=r.randint(1,7);w=r.randint(1,7)
    g=[['#' if r.random()<.3 else '.' for _ in range(w)] for _ in range(h)]
    a,b=r.sample(range(h*w),2) if h*w>1 else (0,0)
    if h*w<2: continue
    g[a//w][a%w]='S';g[b//w][b%w]='E'
    L=[''.join(x) for x in g]
    D={(a//w,a%w):0};q=collections.deque([(a//w,a%w)]);ans=-1
    while q:
        y,x=q.popleft()
        if (y,x)==(b//w,b%w):ans=D[(y,x)];break
        for j,i in((y+1,x),(y-1,x),(y,x+1),(y,x-1)):
            if 0<=j<h and 0<=i<w and L[j][i]!='#' and (j,i) not in D:D[(j,i)]=D[(y,x)]+1;q.append((j,i))
    assert solve(L)==ans,(L,ans)
print("ok")
