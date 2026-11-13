import random, subprocess, sys
def naive(a,b):
    p=[0]*(len(b)+1)
    for x in a:
        c=[0]
        for j,y in enumerate(b):
            c.append(p[j]+1 if x==y else max(p[j+1],c[j]))
        p=c
    return p[-1]
random.seed(1)
for t in range(40):
    n=random.randint(0,60); m=random.randint(0,60)
    al=random.choice(["ab","abc","abcdefghijklmnopqrstuvwxyz"])
    a=''.join(random.choice(al) for _ in range(n)); b=''.join(random.choice(al) for _ in range(m))
    out=subprocess.run([sys.executable,"lcs.py"],input=f"{a}\n{b}\n",capture_output=True,text=True).stdout.strip()
    assert out==str(naive(a,b)),(a,b,out,naive(a,b))
print("OK")
