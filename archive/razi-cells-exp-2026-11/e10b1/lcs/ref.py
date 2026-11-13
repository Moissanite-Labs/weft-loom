import random, subprocess, sys
def dp(a,b):
    prev=[0]*(len(b)+1)
    for x in a:
        cur=[0]
        for j,y in enumerate(b):
            cur.append(prev[j]+1 if x==y else max(prev[j+1],cur[j]))
        prev=cur
    return prev[-1]
random.seed(1)
sys.path.insert(0,'.')
from lcs import lcs
for t in range(2000):
    k=random.choice([1,2,3,4,26])
    al='abcdefghijklmnopqrstuvwxyz'[:k]
    a=''.join(random.choice(al) for _ in range(random.randint(0,40)))
    b=''.join(random.choice(al) for _ in range(random.randint(0,40)))
    assert lcs(a,b)==dp(a,b),(a,b,lcs(a,b),dp(a,b))
print("unit ok")
# CLI checks
def cli(a,b):
    return subprocess.run([sys.executable,'lcs.py'],input=a+'\n'+b+'\n',capture_output=True,text=True).stdout.strip()
assert cli('AGGTAB','GXTXAYB')=='4'
assert cli('','abc')=='0'
assert cli('abc','')=='0'
a=''.join(random.choice('ACGT') for _ in range(3000))
b=''.join(random.choice('ACGT') for _ in range(3000))
open('big.txt','w').write(a+'\n'+b+'\n')
exp=dp(a,b)
open('big.exp','w').write(str(exp))
assert cli(a,b)==str(exp)
print("cli ok",exp)
