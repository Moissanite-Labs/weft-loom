import random, subprocess, sys
sys.path.insert(0,'.')
from lcs import lcs_length

def dp(a,b):
    m=len(b); prev=[0]*(m+1)
    for i in range(1,len(a)+1):
        cur=[0]*(m+1); ai=a[i-1]
        for j in range(1,m+1):
            if ai==b[j-1]: cur[j]=prev[j-1]+1
            else:
                x=prev[j]; y=cur[j-1]; cur[j]= x if x>y else y
        prev=cur
    return prev[m]

random.seed(7)
for _ in range(500):
    n=random.randint(0,60); k=random.randint(0,60)
    a=''.join(random.choice('abcd') for _ in range(n))
    b=''.join(random.choice('abcd') for _ in range(k))
    assert dp(a,b)==lcs_length(a,b),(a,b)
print('rand OK')

cases=[('','',0),('abc','',0),('','abc',0),('abc','abc',3),('abc','ac',2),('AGGTAB','GXTXAYB',4),
       ('aaaa','aa',2),('a'*3000,'a'*3000,3000),('ab'*1500,'ba'*1500,2999)]
for a,b,e in cases:
    g=lcs_length(a,b)
    assert g==e,(len(a),len(b),e,g)
print('edge OK')

def run(s):
    p=subprocess.run([sys.executable,'lcs.py'],input=s,capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    return p.stdout.strip()
assert run('AGGTAB\nGXTXAYB\n')=='4'
assert run('abc\nac\n')=='2'
assert run('abc\n')=='0'
assert run('')=='0'
assert run('\n\n')=='0'
print('CLI OK')
print('ALL VERIFIED')
