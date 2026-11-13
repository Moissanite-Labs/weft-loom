import sys
P=1000000007
def main():
    data=sys.stdin.buffer.read().split()
    M=2*(P+1)
    S=16;K=1<<S;mask=K-1
    f=[0]*(K+2);f[1]=1
    for i in range(2,K+2):
        f[i]=(f[i-1]+f[i-2])%P
    fK,fK1,fKm=f[K],f[K+1],f[K-1]
    H=M>>S
    A=[0]*(H+2);B=[0]*(H+2);a=0;b=1
    for h in range(H+2):
        A[h]=a;B[h]=b
        a,b=(a*fK1+b*fK)%P,(a*fK+b*fKm)%P
    out=[]
    ap=out.append
    for t in data:
        n=int(t)%M
        h=n>>S;l=n&mask
        ap((A[h]*f[l+1]+B[h]*f[l])%P)
    sys.stdout.write("\n".join(map(str,out))+("\n" if out else ""))
main()
