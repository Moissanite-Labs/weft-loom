import sys
M=1000000007
P=2*(M+1)
S=16
K=1<<S
L=[0]*(K+2)
L[1]=1
for i in range(2,K+2):L[i]=(L[i-1]+L[i-2])%M
FK,FK1=L[K],L[K+1]
FK0=(FK1-FK)%M
H=[0]*(P>>S+2)
m,m1=0,1
H0=[0]*(P//K+2)
H1=[0]*(P//K+2)
m,m1=0,M-0  # F(0)=0,F(-1)=1
m1=1
for h in range(P//K+2):
    H0[h]=m;H1[h]=m1
    m,m1=(m*L[K+1]+m1*FK)%M,(m*FK+m1*FK0)%M
def main():
    out=[]
    for x in sys.stdin.read().split():
        n=int(x)%P
        h=n>>S;l=n&(K-1)
        out.append((H0[h]*L[l+1]+H1[h]*L[l])%M)
    print("\n".join(map(str,out)))
main()
