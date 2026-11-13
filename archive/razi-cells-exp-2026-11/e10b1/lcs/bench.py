import random, time, sys
sys.path.insert(0,'.')
import lcs as L1, lcs2 as L2
def dp(a,b):
    prev=[0]*(len(b)+1)
    for x in a:
        cur=[0]
        for j,y in enumerate(b):
            cur.append(prev[j]+1 if x==y else max(prev[j+1],cur[j]))
        prev=cur
    return prev[-1]
random.seed(5)
for t in range(3000):
    k=random.choice([1,2,3,4,26])
    al='abcdefghijklmnopqrstuvwxyz\u00e9\u4e2d'[:k] if t%3 else 'ab\u00e9\u4e2dxyz'
    a=''.join(random.choice(al) for _ in range(random.randint(0,40)))
    b=''.join(random.choice(al[:random.randint(1,len(al))]) for _ in range(random.randint(0,40)))
    for K in (1,3,64):
        assert L2.lcs(a,b,K)==dp(a,b),(a,b)
for t in range(20):
    a=''.join(random.choice('abcdefgh') for _ in range(random.randint(100,400)))
    b=''.join(random.choice('abcdefghij') for _ in range(random.randint(100,400)))
    assert L2.lcs(a,b)==dp(a,b)
print('ok')
big=open('big.txt').read(); a,b=big.split('\n')[:2]; e=int(open('big.exp').read())
def bench(f):
    best=1e9
    for _ in range(5):
        t=time.perf_counter()
        for _ in range(100):
            assert f(a,b)==e
        best=min(best,time.perf_counter()-t)
    return round(100/best,1)
print('old',bench(L1.lcs))
for K in (16,32,64,128,256):
    print(K,bench(lambda x,y:L2.lcs(x,y,K)))
