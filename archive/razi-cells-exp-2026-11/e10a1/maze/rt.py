import random, subprocess, sys
from collections import deque
r = random.Random(7)
def ref(rows):
    for i,row in enumerate(rows):
        for j,ch in enumerate(row):
            if ch=='S': s=(i,j)
            if ch=='E': e=(i,j)
    dist={s:0}; q=deque([s])
    while q:
        i,j=q.popleft()
        if (i,j)==e: return dist[e]
        for x,y in ((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
            if 0<=x<len(rows) and 0<=y<len(rows[x]) and rows[x][y]!='#' and (x,y) not in dist:
                dist[(x,y)]=dist[(i,j)]+1; q.append((x,y))
    return -1
bad=0
for t in range(160):
    n=r.randint(1,14); m=r.randint(2 if n==1 else 1,14); p=r.choice([0,0.2,0.3,0.4,0.5])
    rows=[[('#' if r.random()<p else '.') for _ in range(m)] for _ in range(n)]
    cells=[(i,j) for i in range(n) for j in range(m)]
    s,e=r.sample(cells,2)
    rows[s[0]][s[1]]='S'; rows[e[0]][e[1]]='E'
    rows=[''.join(x) for x in rows]
    sep=r.choice(['\n','\n','\r\n']); txt=sep.join(rows)+r.choice(['',sep])
    out=subprocess.run([sys.executable,'maze2.py'],input=txt.encode(),capture_output=True).stdout.decode().strip()
    if out!=str(ref(rows)):
        bad+=1; print('MISMATCH',repr(txt),out,ref(rows))
        if bad>3: break
print('bad',bad)
