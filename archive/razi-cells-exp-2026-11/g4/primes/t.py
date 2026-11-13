import time
from math import isqrt
N=5000000
EXPECT={10:4,100:25,1000:168,30:10,999983:78497,1000000:78498,5000000:348513,3:1,4:2,1:0,2:1,5:2,6:3,7:4,8:4,13:5,25:9,49:15,100000:9592}

def odd_sum(n):
    size=n>>1
    s=bytearray(size); s[0]=1
    r=isqrt(n-1)
    for i in range(1,(r-1)//2+1):
        if not s[i]:
            p=2*i+1; st=p*p>>1
            s[st::p]=b'\x01'*(((size-st-1)//p)+1)
    return 1+size-sum(s)

def odd_cnt(n):
    size=n>>1
    s=bytearray(size); s[0]=1
    r=isqrt(n-1)
    for i in range(1,(r-1)//2+1):
        if not s[i]:
            p=2*i+1; st=p*p>>1
            s[st::p]=b'\x01'*(((size-st-1)//p)+1)
    return 1+size-s.count(1)

ONES=b'\x01'*(N>>1)
def odd_cnt_pre(n):
    size=n>>1
    s=bytearray(size); s[0]=1
    r=isqrt(n-1)
    for i in range(1,(r-1)//2+1):
        if not s[i]:
            p=2*i+1; st=p*p>>1
            s[st::p]=ONES[:((size-st-1)//p)+1]
    return 1+size-s.count(1)

def w6(n):
    na=(n+4)//6; nb=n//6
    a=bytearray(na); b=bytearray(nb)
    if na: a[0]=1
    lim=isqrt(n-1)
    for i in range(na):
        p=6*i+1
        if p>lim: break
        if not a[i]:
            inv=pow(6,-1,p); ra=(-inv)%p; rb=(-5*inv)%p
            lo=(p*p-1)//6
            ia=lo+((ra-lo)%p)
            qb=p+2 if p%6==5 else p+4
            ib0=(p*qb-5)//6
            ib=ib0+((rb-ib0)%p)
            ca=(na-ia+p-1)//p
            if ca>0: a[ia::p]=b'\x01'*ca
            cb=(nb-ib+p-1)//p
            if cb>0: b[ib::p]=b'\x01'*cb
    for i in range(nb):
        p=6*i+5
        if p>lim: break
        if not b[i]:
            inv=pow(6,-1,p); ra=(-inv)%p; rb=(-5*inv)%p
            lo=(p*p-1)//6
            ia=lo+((ra-lo)%p)
            qb=p+2 if p%6==5 else p+4
            ib0=(p*qb-5)//6
            ib=ib0+((rb-ib0)%p)
            ca=(na-ia+p-1)//p
            if ca>0: a[ia::p]=b'\x01'*ca
            cb=(nb-ib+p-1)//p
            if cb>0: b[ib::p]=b'\x01'*cb
    return (1 if n>2 else 0)+(1 if n>3 else 0)+(na-a.count(1))+(nb-b.count(1))

for f in (odd_sum, odd_cnt, odd_cnt_pre, w6):
    bad=[(n,e,f(n)) for n,e in EXPECT.items() if f(n)!=e]
    print(f.__name__, 'BAD:'+str(bad[:4]) if bad else 'ok', end='  ')
    t0=time.perf_counter()
    for _ in range(5): f(N)
    print(round((time.perf_counter()-t0)/5*1000,2),'ms')
