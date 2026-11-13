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
for t in range(40):
    n=random.randint(0,60); m=random.randint(0,60)
    al=random.choice(["ab","abc","abcdefghij"])
    a="".join(random.choice(al) for _ in range(n)); b="".join(random.choice(al) for _ in range(m))
    out=subprocess.run([sys.executable,"lcs.py"],input=f"{a}\n{b}\n",capture_output=True,text=True).stdout.strip()
    assert int(out)==naive(a,b),(a,b,out,naive(a,b))
print("ok")
