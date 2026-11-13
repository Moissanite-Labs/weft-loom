import sys
def main():
    P=1000000007
    data=sys.stdin.buffer.read().split()
    M=2*(P+1)
    h=(P+1)//2
    ga=gb=h
    LA=[1];LB=[0]
    a=1;b=0
    for _ in range(65535):
        a,b=(a*ga+5*b*gb)%P,(a*gb+b*ga)%P
        LA.append(a);LB.append(b)
    sa=(a*ga+5*b*gb)%P;sb=(a*gb+b*ga)%P
    HA=[1];HB=[0]
    a=1;b=0
    for _ in range(M>>16):
        a,b=(a*sa+5*b*sb)%P,(a*sb+b*sa)%P
        HA.append(a);HB.append(b)
    out=[]
    ap=out.append
    for t in data:
        n=int(t)%M
        i=n&65535;j=n>>16
        ap((2*(HA[j]*LB[i]+LA[i]*HB[j]))%P)
    sys.stdout.write("\n".join(map(str,out))+"\n" if out else "")
main()
