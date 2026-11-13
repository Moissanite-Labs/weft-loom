import random,subprocess,time,sys,os
from collections import deque
N=2000
random.seed(7)
g=[['#' if random.random()<0.28 else '.' for _ in range(N)] for _ in range(N)]
g[0][0]='S'; g[N-1][N-1]='E'
rows=[''.join(r) for r in g]
txt='\n'.join(rows)+'\n'
def ref():
    d={(0,0):0};q=deque([(0,0)])
    while q:
        x,y=q.popleft()
        if (x,y)==(N-1,N-1): return d[(x,y)]
        for a,b in((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0<=a<N and 0<=b<N and rows[a][b]!='#' and (a,b) not in d:
                d[(a,b)]=d[(x,y)]+1;q.append((a,b))
    return -1
exp=ref()
t=time.time()
o=subprocess.run([sys.executable,'maze.py'],input=txt,capture_output=True,text=True).stdout.strip()
t=time.time()-t
print(1/t if o==str(exp) else 0)
