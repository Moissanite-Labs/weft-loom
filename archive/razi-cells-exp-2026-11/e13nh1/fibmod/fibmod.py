import sys
M=1000000007
L=65536
f=[0,1]
for i in range(L+1):f.append((f[-1]+f[-2])%M)
A=f[L];B=f[L+1];C=(B-A)%M  # F(L),F(L+1),F(L-1)
H=[(0,1)]
a,b=0,1
for h in range(30600):
    # F(x+L)=F(x)F(L+1)+F(x-1)F(L)
    a,b=(a*B+(b-a)*A)%M,(b*B+a*A)%M
    H.append((a,b))
out=[]
for x in sys.stdin.read().split():
    n=int(x)%2000000016
    p,q=H[n>>16];l=n&65535
    out.append((p*f[l+1]+(q-p)*f[l])%M)
print("\n".join(map(str,out)))
