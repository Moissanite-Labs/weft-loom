import random, time, sys, subprocess
import lcs as L
def naive(a,b):
    m=len(b); prev=[0]*(m+1)
    for x in a:
        cur=[0]*(m+1)
        for j in range(m):
            cur[j+1]=prev[j]+1 if x==b[j] else max(prev[j+1],cur[j])
        prev=cur
    return prev[m]
random.seed(3)
for t in range(40):
    n=random.randint(0,80); m=random.randint(0,80)
    a=''.join(random.choice('abc') for _ in range(n)); b=''.join(random.choice('abc') for _ in range(m))
    if L.lcs(a,b)!=naive(a,b): print(0); sys.exit(1)
random.seed(7)
a=''.join(random.choice('ACGT') for _ in range(3000)); b=''.join(random.choice('ACGT') for _ in range(3000))
out=subprocess.run([sys.executable,'lcs.py'],input=a+'\n'+b+'\n',capture_output=True,text=True).stdout.strip()
if out!='1948': print(0); sys.exit(1)
random.seed(11)
a=''.join(random.choice('ACGT') for _ in range(30000)); b=''.join(random.choice('ACGT') for _ in range(30000))
ref=L.lcs(a,b)
ts=[]
for rep in range(31):
    t0=time.perf_counter()
    r=L.lcs(a,b)
    dt=time.perf_counter()-t0
    if r!=ref: print(0); sys.exit(1)
    ts.append(dt)
ts.sort()
med=sum(ts[:8])/8
print(round(1000/med,1))
