import sys
M=1000000007
P=2*(M+1)
H=65536
f=[0,1]
for i in range(H+1):f.append((f[-1]+f[-2])%M)
FH=f[H];FH1=f[H+1]
J=P//H+2
A=[0]*J;C=[0]*J
a,b=0,1
for j in range(J):
    A[j]=a;C[j]=(b-a)%M
    a,b=(a*FH1+(b-a)*FH)%M,(a*FH+b*FH1)%M
out=[]
c={}
for t in sys.stdin.buffer.read().split():
    r=c.get(t)
    if r is None:
        n=int(t)%P
        j=n>>16;l=n&65535
        r=c[t]=str((A[j]*f[l+1]+C[j]*f[l])%M)
    out.append(r)
print("\n".join(out))
