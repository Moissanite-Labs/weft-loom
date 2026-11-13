import sys
P=1000000007
Q=2*(P+1)
S=16
B=1<<S
def main():
    data=sys.stdin.read().split()
    ns=[int(x)%Q for x in data]
    mx=max(ns) if ns else 0
    F=[0]*(B+2);F[1]=1
    for i in range(2,B+2):F[i]=(F[i-1]+F[i-2])%P
    fb,fb1,fbm=F[B],F[B+1],F[B-1]
    nh=(mx>>S)+1
    h0=[0]*nh;h1=[0]*nh  # F(H),F(H-1)
    h1[0]=1
    a,c=0,1
    for i in range(1,nh):
        a,c=(a*fb1+c*fb)%P,(a*fb+c*fbm)%P
        h0[i]=a;h1[i]=c
    m=B-1
    out=[]
    for n in ns:
        h=n>>S;l=n&m
        out.append((h0[h]*F[l+1]+h1[h]*F[l])%P)
    sys.stdout.write("\n".join(map(str,out))+("\n" if out else ""))
main()
