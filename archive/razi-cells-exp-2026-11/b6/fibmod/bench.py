import random, time, subprocess, sys
from fibmod import fib
P = 1000000007

def reference(n):
    def mul(x, y):
        a,b,c,d=x; e,f,g,h=y
        return ((a*e+b*g)%P,(a*f+b*h)%P,(c*e+d*g)%P,(c*f+d*h)%P)
    a=(1,0,0,1); b=(1,1,1,0)
    while n:
        if n&1: a=mul(a,b)
        b=mul(b,b); n>>=1
    return a[1]

rng=random.Random(731)
cases=list(range(150))+[10**18,10**18-1,1000000007,1000000008,2000000016,2000000017]+[rng.randrange(10**18+1) for _ in range(120)]
for n in cases:
    if fib(n)!=reference(n):
        print(0); sys.exit(0)
for n in [0,1,10,2000000016,10**18]:
    if subprocess.check_output([sys.executable,'fibmod.py',str(n)]).strip()!=str(reference(n)).encode():
        print(0); sys.exit(0)
inputs=[rng.randrange(10**18+1) for _ in range(1000000)]
t=time.perf_counter()
for n in inputs: fib(n)
elapsed=time.perf_counter()-t
print(1/elapsed)
