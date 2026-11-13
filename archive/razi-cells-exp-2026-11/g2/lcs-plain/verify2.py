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
                x=prev[j]; y=cur[j-1]; cur[j]=x if x>y else y
        prev=cur
    return prev[m]

# edge cases
assert lcs_length('','')==0
assert lcs_length('abc','')==0
assert lcs_length('','abc')==0
assert lcs_length('abc','abc')==3
assert lcs_length('a','a')==1
assert lcs_length('abcde','ace')==3
assert lcs_length('aaaa','aa')==2
print('edge OK')

random.seed(7)
for t in range(2000):
    n=random.randint(0,60); k=random.randint(0,60)
    al=random.choice(['ab','abcd','abcdefgh','abcdefghijklmnopqrstuvwxyz'])
    a=''.join(random.choice(al) for _ in range(n))
    b=''.join(random.choice(al) for _ in range(k))
    e=dp(a,b); g=lcs_length(a,b)
    if e!=g:
        print('FAIL',repr(a),repr(b),e,g); sys.exit(1)
print('random 2000 OK')

# identical 3000-char strings (worst case, matches everywhere)
s=''.join(random.choice('abcdefghij') for _ in range(3000))
assert lcs_length(s,s)==3000
assert lcs_length(s,s[::-1])==dp(s,s[::-1])
print('3000 identical OK, reversed matches dp')

# CLI end-to-end
p=subprocess.run([sys.executable,'lcs.py'],input='ABCBDAB\nBDCABA\n',capture_output=True,text=True)
assert p.stdout.strip()=='4', p.stdout
p=subprocess.run([sys.executable,'lcs.py'],input='\n\n',capture_output=True,text=True)
assert p.stdout.strip()=='0'
print('CLI OK')
print('ALL VERIFIED')
