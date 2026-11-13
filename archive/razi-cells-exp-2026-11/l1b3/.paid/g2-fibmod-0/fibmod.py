import sys
M=1000000007
P=2*(M+1)
def comb(x,y):
    a1,b1=x;a2,b2=y
    return ((a1*b2+(b1-a1)*a2)%M,(b1*b2+a1*a2)%M)
def fd(n):
    if n==0:return (0,1)
    a,b=fd(n>>1)
    c=a*(2*b-a)%M;d=(a*a+b*b)%M
    return (d,(c+d)%M) if n&1 else (c,d)
T=[]
for k in range(3):
    base=fd(1<<(11*k));t=[(0,1)]
    for v in range(2047):t.append(comb(t[-1],base))
    T.append(t)
T0,T1,T2=T
def main():
    c={};o=[]
    for s in sys.stdin.read().split():
        r=c.get(s)
        if r is None:
            n=int(s)%P
            a1,b1=T0[n&2047];a2,b2=T1[(n>>11)&2047]
            x=(a1*b2+(b1-a1)*a2)%M;y=(b1*b2+a1*a2)%M
            a2,b2=T2[n>>22]
            r=c[s]=str((x*b2+(y-x)*a2)%M)
        o.append(r)
    print("\n".join(o))
main()
