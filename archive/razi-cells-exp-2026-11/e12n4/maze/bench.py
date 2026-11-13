import random,subprocess,sys,time,collections
n=2000
random.seed(7)
g=[['#' if random.random()<0.28 else '.' for _ in range(n)] for _ in range(n)]
g[0][0]='S'; g[n-1][n-1]='E'
txt="\n".join("".join(r) for r in g)+"\n"
t=time.time()
out=subprocess.run([sys.executable,"maze.py"],input=txt,capture_output=True,text=True).stdout.strip()
dt=time.time()-t
# reference BFS
dist={(0,0):0};q=collections.deque([(0,0)]);ref=-1
while q:
    x,y=q.popleft()
    if (x,y)==(n-1,n-1): ref=dist[(x,y)];break
    for a,b in((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
        if 0<=a<n and 0<=b<n and g[a][b]!='#' and (a,b) not in dist:
            dist[(a,b)]=dist[(x,y)]+1;q.append((a,b))
print(1/dt if out==str(ref) else 0)
