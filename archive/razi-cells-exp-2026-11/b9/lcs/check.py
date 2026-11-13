import random, subprocess, sys
def naive(a,b):
    m=len(b); prev=[0]*(m+1)
    for x in a:
        cur=[0]*(m+1)
        for j in range(m):
            cur[j+1]=prev[j]+1 if x==b[j] else max(prev[j+1],cur[j])
        prev=cur
    return prev[m]
random.seed(1)
for t in range(30):
    n=random.randint(0,60); m=random.randint(0,60)
    a=''.join(random.choice('abc') for _ in range(n)); b=''.join(random.choice('abc') for _ in range(m))
    out=subprocess.run([sys.executable,'lcs.py'],input=a+'\n'+b+'\n',capture_output=True,text=True).stdout.strip()
    assert int(out)==naive(a,b),(a,b,out)
print("ok")
