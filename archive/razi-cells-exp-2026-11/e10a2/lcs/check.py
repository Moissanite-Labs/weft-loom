import random, subprocess, sys
from ref import ref
from lcs import lcs
random.seed(1)
for t in range(3000):
    k=random.choice([1,2,3,4,26])
    a=''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(random.randint(0,30)))
    b=''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(random.randint(0,30)))
    assert lcs(a,b)==ref(a,b),(a,b)
# CLI checks
def run(s):
    return subprocess.run([sys.executable,'lcs.py'],input=s,capture_output=True,text=True).stdout.strip()
assert run("ABCBDAB\nBDCABA\n")=="4"
assert run("abc\n\n")=="0"
assert run("\n")=="0"
assert run("")=="0"
assert run("abc\r\nabc\r\n")=="3"
assert run("abc\nabc")=="3"
random.seed(7)
a=''.join(random.choice('ACGT') for _ in range(3000))
b=''.join(random.choice('ACGT') for _ in range(3000))
open('big.txt','w').write(a+"\n"+b+"\n")
r=ref(a,b)
open('big.ans','w').write(str(r))
assert run(a+"\n"+b+"\n")==str(r)
print("ok",r)
