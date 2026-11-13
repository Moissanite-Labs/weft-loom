import random, subprocess, sys
def naive(a,b):
    prev=[0]*(len(b)+1)
    for x in a:
        cur=[0]
        for j,y in enumerate(b):
            cur.append(prev[j]+1 if x==y else max(prev[j+1],cur[j]))
        prev=cur
    return prev[-1]
random.seed(1)
cases=[("",""),("abc",""),("abc","abc"),("abcde","ace")]
for _ in range(30):
    n=random.randint(0,60); m=random.randint(0,60)
    k=random.choice([2,4,26])
    cases.append((''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(n)),
                  ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(m))))
for a,b in cases:
    out=subprocess.run([sys.executable,'lcs.py'],input=a+"\n"+b+"\n",capture_output=True,text=True).stdout.strip()
    assert out==str(naive(a,b)),(a,b,out,naive(a,b))
print("OK")
