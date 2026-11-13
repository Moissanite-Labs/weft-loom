import sys
M=1000000007
P=2*(M+1)
K=1<<16
# tables: A[a]=(F(aK),F(aK-1)); B[b]=F(b)
def mk(m):
    # F(m),F(m-1) by doubling
    a,b=0,1  # F(0),F(1)
    for c in bin(m)[2:]:
        d=a*((2*b-a)%M)%M
        e=(a*a+b*b)%M
        if c=='1': a,b=e,(d+e)%M
        else: a,b=d,e
    return a,b
f0,f1=mk(K)       # F(K),F(K+1)
fk=f0; fk1=(f1-f0)%M  # F(K),F(K-1)
H=(P>>16)+2
A=[0]*H;A1=[0]*H
A[0]=0;A1[0]=1  # F(0)=0,F(-1)=1
# F(x+K)=F(x)F(K+1)+F(x-1)F(K)
for i in range(1,H):
    x,y=A[i-1],A1[i-1]
    A[i]=(x*f1+y*fk)%M
    A1[i]=(x*fk+y*fk1)%M  # F(x+K-1)=F(x)F(K)+F(x-1)F(K-1)
B=[0]*(K+2);B[1]=1
for i in range(2,K+2):B[i]=(B[i-1]+B[i-2])%M
out=[]
for t in sys.stdin.read().split():
    n=int(t)%P
    a=n>>16;b=n&65535
    out.append((A[a]*B[b+1]+A1[a]*B[b])%M)
print("\n".join(map(str,out)))
