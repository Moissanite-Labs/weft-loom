import sys
M=1000000007
def pr(n):
    a,b=0,1
    for c in bin(n)[2:]:
        t=a*(2*b-a)%M
        u=(a*a+b*b)%M
        if c=='1':a,b=u,(t+u)%M
        else:a,b=t,u
    return a,b
def tab(S):
    s=pr(S);s0,s1=s
    T=[(0,1)];a,b=0,1
    for _ in range(2047):
        a,b=(a*s1+(b-a)*s0)%M,(a*s0+b*s1)%M
        T.append((a,b))
    return T
T0=[(0,1)];a,b=0,1
for _ in range(2047):
    a,b=b,(a+b)%M;T0.append((a,b))
T1=tab(2048);T2=tab(1<<22)
P=2*M+2
out=[]
for x in sys.stdin.read().split():
    n=int(x)%P
    a0,a1=T2[n>>22]
    b0,b1=T1[(n>>11)&2047]
    a0,a1=(a0*b1+(a1-a0)*b0)%M,(a0*b0+a1*b1)%M
    b0,b1=T0[n&2047]
    out.append((a0*b1+(a1-a0)*b0)%M)
print("\n".join(map(str,out)))
