import random, subprocess, sys, time
sys.path.insert(0,'.')
from lcs import lcs_length

def dp(a,b):
    m=len(b); prev=[0]*(m+1)
    for i in range(1,len(a)+1):
        cur=[0]*(m+1); ai=a[i-1]
        for j in range(1,m+1):
            if ai==b[j-1]: cur[j]=prev[j-1]+1
            else:
                x=prev[j]; y=cur[j-1]; cur[j]=x if x>y else y
        prev=cur
    return prev[m]

random.seed(7)
for t in range(60):
    n=random.randint(0,120); k=random.randint(0,120)
    alpha=random.choice(['ab','abcd','abcdefgh'])
    a=''.join(random.choice(alpha) for _ in range(n))
    b=''.join(random.choice(alpha) for _ in range(k))
    e=dp(a,b); g=lcs_length(a,b)
    if e!=g:
        print('FAIL',repr(a),repr(b),e,g); sys.exit(1)
print('dp-match OK')

# stdin interface test
p=subprocess.run([sys.executable,'lcs.py'],input='AGGTAB\nGXTXAYB\n',capture_output=True,text=True)
assert p.stdout.strip()=='4', p.stdout
p=subprocess.run([sys.executable,'lcs.py'],input='\n\n',capture_output=True,text=True)
assert p.stdout.strip()=='0', p.stdout
print('cli OK')

for alpha in ['ab','abcdefghij','abcdefghijklmnopqrstuvwxyz']:
    a=''.join(random.choice(alpha) for _ in range(3000))
    b=''.join(random.choice(alpha) for _ in range(3000))
    t0=time.time(); r=lcs_length(a,b); dt=time.time()-t0
    print('alpha len',len(alpha),'result',r,'time',round(dt,4))
