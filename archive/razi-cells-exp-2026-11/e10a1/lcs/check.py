import random, subprocess, sys
def ref(a,b):
    n=len(b); prev=[0]*(n+1)
    for x in a:
        cur=[0]*(n+1)
        for j in range(n):
            cur[j+1]=prev[j]+1 if x==b[j] else max(prev[j+1],cur[j])
        prev=cur
    return prev[n]
random.seed(1)
cases=[("",""),("a",""),("","b"),("abc","abc"),("abc","def"),("AGGTAB","GXTXAYB")]
for _ in range(60):
    k=random.choice([2,4,26]); alpha="abcdefghijklmnopqrstuvwxyz"[:k]
    cases.append(("".join(random.choice(alpha) for _ in range(random.randint(0,60))),"".join(random.choice(alpha) for _ in range(random.randint(0,60)))))
for k in (2,4,26):
    alpha="abcdefghijklmnopqrstuvwxyz"[:k]
    cases.append(("".join(random.choice(alpha) for _ in range(700)),"".join(random.choice(alpha) for _ in range(900))))
bad=0
for a,b in cases:
    out=subprocess.run([sys.executable,"lcs.py"],input=(a+"\n"+b+"\n").encode(),capture_output=True).stdout.decode().strip()
    if out!=str(ref(a,b)):
        bad+=1; print("MISMATCH",repr(a[:20]),repr(b[:20]),out,ref(a,b))
print("cases",len(cases),"bad",bad)
