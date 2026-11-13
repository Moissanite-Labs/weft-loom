import time, random
MOD=1000000007; PER=2000000016
def fd(n):
    a,b=0,1
    for bit in bin(n)[2:]:
        c=a*((b+b-a)%MOD)%MOD
        d=(a*a+b*b)%MOD
        if bit=='0': a,b=c,d
        else: a,b=d,(c+d)%MOD
    return a,b
def build(nl,bits):
    tabs=[]
    for j in range(nl):
        s=1<<(bits*j)
        a,b=fd(s)
        tab=[(0,1)]
        x,y=0,1
        for k in range(1,1<<bits):
            x,y=(y*a+x*(b-a))%MOD,(y*b+x*a)%MOD
            tab.append((x,y))
        tabs.append(tab)
    return tabs

t0=time.perf_counter(); T311=build(3,11); print("build 3x11",time.perf_counter()-t0)
t0=time.perf_counter(); T48=build(4,8); print("build 4x8",time.perf_counter()-t0)
t0=time.perf_counter(); T215=build(2,15); print("build 2x15(32768,32768)",time.perf_counter()-t0, len(T215[1]))

def fib_naive_double(n, MOD=MOD, PER=PER):
    n%=PER
    a,b=0,1
    for bit in bin(n)[2:]:
        c=a*((b+b-a)%MOD)%MOD
        d=(a*a+b*b)%MOD
        if bit=='0': a,b=c,d
        else: a,b=d,c+d if c+d<MOD else c+d-MOD
    return a

A0,A1,A2=T311
def fib3(n, MOD=MOD, PER=PER, A0=A0, A1=A1, A2=A2):
    n%=PER
    a,b=A0[n&2047]
    c,d=A1[(n>>11)&2047]
    a,b=(b*c+a*(d-c))%MOD,(b*d+a*c)%MOD
    c,d=A2[n>>22]
    return (b*c+a*(d-c))%MOD

B0,B1,B2,B3=T48
def fib4(n, MOD=MOD, PER=PER, B0=B0, B1=B1, B2=B2, B3=B3):
    n%=PER
    a,b=B0[n&255]
    c,d=B1[(n>>8)&255]
    a,b=(b*c+a*(d-c))%MOD,(b*d+a*c)%MOD
    c,d=B2[(n>>16)&255]
    a,b=(b*c+a*(d-c))%MOD,(b*d+a*c)%MOD
    c,d=B3[n>>24]
    return (b*c+a*(d-c))%MOD

C0,C1=T215
def fib2(n, MOD=MOD, PER=PER, C0=C0, C1=C1):
    n%=PER
    a,b=C0[n&32767]
    c,d=C1[n>>15]
    return (b*c+a*(d-c))%MOD

def fib2c(n, MOD=MOD, PER=PER, C0=C0, C1=C1):
    n%=PER
    a,b=C0[n&32767]
    c,d=C1[n>>15]
    return (b*d+a*c)%MOD

# correctness
naive=[0,1]
for i in range(2,3000): naive.append((naive[-1]+naive[-2])%MOD)
for n in range(3000):
    assert fib3(n)==naive[n] and fib4(n)==naive[n] and fib2(n)==naive[n], n
for n in [10,10**18,10**18-1,PER-1,PER,PER+5,2**31-1,0]:
    assert fib3(n)==fib_naive_double(n)==fib4(n)==fib2(n), (n,fib3(n),fib_naive_double(n))
print("correct", fib3(10), fib3(10**18))
random.seed(1)
ns=[random.randrange(10**18) for _ in range(200000)]
for name,f in [("dbl",fib_naive_double),("f3",fib3),("f4",fib4),("f2",fib2),("f2c",fib2c)]:
    t0=time.perf_counter(); s=0
    for n in ns: s+=f(n)
    dt=time.perf_counter()-t0
    print(name, round(dt,3), "us/call", round(dt/len(ns)*1e6,3), s%MOD)
