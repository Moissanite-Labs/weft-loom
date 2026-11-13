import sys
M=1000000007
def fib(n):
    a,b=0,1
    for i in range(n.bit_length()-1,-1,-1):
        c=a*((2*b-a)%M)%M
        d=(a*a+b*b)%M
        if n>>i&1:
            a,b=d,(c+d)%M
        else:
            a,b=c,d
    return a,(a+b)%M if False else b
P=2*(M+1)
S=1<<16
data=sys.stdin.read().split()
ns=[int(x)%P for x in data]
if len(ns)<300:
    print("\n".join(str(fib(n)[0]) for n in ns))
else:
    A0=[0]*S;A1=[0]*S
    a,b=0,1
    for i in range(S):
        A0[i]=a;A1[i]=b
        a,b=b,(a+b)%M
    s0,s1=fib(S)
    sm=(s1-s0)%M
    H=(P>>16)+1
    B0=[0]*H;B1=[0]*H
    x,y=0,1
    for i in range(H):
        B0[i]=x;B1[i]=y
        # F(h+S)=x*s1+(y-x)*s0 ; F(h+S+1)=F(h+1+S)
        x,y=(x*s1+(y-x)*s0)%M,(y*s1+(x)*s0)%M
    out=[]
    for n in ns:
        h=n>>16;l=n&65535
        out.append((B0[h]*A1[l]+(B1[h]-B0[h])*A0[l])%M)
    print("\n".join(map(str,out)))
