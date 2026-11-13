import sys
P=1000000007
def comb(x,y):
    x0,x1=x;y0,y1=y
    return ((x0*y1+(x1-x0)*y0)%P,(x1*y1+x0*y0)%P)
def fd(n):
    a,b=0,1
    for c in bin(n)[2:]:
        t=a*(2*b-a)%P;u=(a*a+b*b)%P
        a,b=(u,(t+u)%P) if c=='1' else (t,u)
    return a,b
def main():
    M=2*(P+1);B=11;S=1<<B
    T=[]
    for j in range(3):
        g=fd(1<<(B*j));cur=(0,1);t=[]
        for k in range(S):
            t.append(cur);cur=comb(cur,g)
        T.append(t)
    T0=[a for a,b in T[0]];T0b=[b for a,b in T[0]]
    T1,T2=T[1],T[2];m=S-1
    out=[];cache={}
    for l in sys.stdin.read().split():
        n=int(l)%M
        x0,x1=T1[(n>>11)&m]
        y0,y1=T2[n>>22]
        z0=(x0*y1+(x1-x0)*y0)%P;z1=(x1*y1+x0*y0)%P
        w=n&m
        out.append((z0*T0b[w]+(z1-z0)*T0[w])%P)
    print("\n".join(map(str,out)))
main()
