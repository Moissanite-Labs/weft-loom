import random, subprocess, sys, time
from collections import deque

def ref(lines):
    H=len(lines); W=len(lines[0])
    S=E=None
    for r in range(H):
        for c in range(W):
            ch=lines[r][c]
            if ch=='S': S=(r,c)
            elif ch=='E': E=(r,c)
    if S is None or E is None: return -1
    dq=deque([(S[0],S[1],0)])
    seen={S}
    while dq:
        r,c,d=dq.popleft()
        if (r,c)==E: return d
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr,nc=r+dr,c+dc
            if 0<=nr<H and 0<=nc<W and (nr,nc) not in seen and lines[nr][nc]!='#':
                seen.add((nr,nc)); dq.append((nr,nc,d+1))
    return -1

def run(inp):
    if isinstance(inp,str): inp=inp.encode()
    p=subprocess.run([sys.executable,'maze.py'],input=inp,capture_output=True)
    return p.stdout.decode().strip()

fails=0
cases=[("S",-1),("SE",1),("S#E",-1),("S.\n.E",2),("S..\n###\n..E",-1),("S..\n...\n..E",4)]
for s,exp in cases:
    g=run(s)
    if g!=str(exp):
        print("FAIL",repr(s),exp,g); fails+=1
print("edges","ok" if fails==0 else "done")

random.seed(12345)
for t in range(300):
    H=random.randint(1,12); W=random.randint(1,12)
    if H*W<2: W=2
    cells=[['.' if random.random()<0.7 else '#' for _ in range(W)] for _ in range(H)]
    sr=random.randrange(H); sc=random.randrange(W)
    er=random.randrange(H); ec=random.randrange(W)
    while (er,ec)==(sr,sc):
        er=random.randrange(H); ec=random.randrange(W)
    cells[sr][sc]='S'; cells[er][ec]='E'
    lines=[''.join(r) for r in cells]
    exp=ref(lines)
    inp='\n'.join(lines)
    g=run(inp)
    if g!=str(exp):
        print("RFAIL",repr(inp),exp,g); fails+=1; break
print("random","ok" if fails==0 else "FAIL")

N=2000
random.seed(999)
rows=[]
for r in range(N):
    rows.append(bytes(46 if random.random()<0.75 else 35 for _ in range(N)))
rows[0]=b'S'+rows[0][1:]
rows[N-1]=rows[N-1][:N-1]+b'E'
inp=b'\n'.join(rows)
t0=time.time()
out=run(inp)
dt=time.time()-t0
print(f"large time {dt:.3f} out {out}")
print("correctness","PASS" if fails==0 else "FAIL")
print("score", round(1/dt,4) if fails==0 and out.lstrip('-').isdigit() else 0)
