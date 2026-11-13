import random, subprocess, sys
from lcs import lcs
def ref(a,b):
    prev=[0]*(len(b)+1)
    for x in a:
        cur=[0]
        for j,y in enumerate(b):
            cur.append(prev[j]+1 if x==y else max(prev[j+1],cur[j]))
        prev=cur
    return prev[-1]
random.seed(1)
for t in range(3000):
    k=random.choice([1,2,3,4,26])
    a=''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(random.randint(0,40)))
    b=''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(random.randint(0,40)))
    assert lcs(a,b)==ref(a,b),(a,b)
a=''.join(random.choice('ACGT') for _ in range(3000))
b=''.join(random.choice('ACGT') for _ in range(3000))
r=ref(a,b)
open('big.txt','w').write(a+'\n'+b+'\n')
open('big.exp','w').write(str(r)+'\n')
out=subprocess.run([sys.executable,'lcs.py'],input=a+'\n'+b+'\n',capture_output=True,text=True).stdout
assert out.strip()==str(r),(out,r)
for inp,exp in [('abc\nabc\n','3'),('\n\n','0'),('abc\n','0'),('abcde\r\nace\r\n','3'),('','0'),('abc\nxyz','0')]:
    out=subprocess.run([sys.executable,'lcs.py'],input=inp,capture_output=True,text=True).stdout.strip()
    assert out==exp,(inp,out,exp)
print('ok',r)
