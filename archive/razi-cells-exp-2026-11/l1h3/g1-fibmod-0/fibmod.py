import sys
M=10**9+7
def main():
    B=12;K=1<<B;T=[]
    # base for chunk i: (F(2^(Bi)),F(+1))
    a,b=0,1  # F(0),F(1)
    ba,bb=1,1  # F(1),F(2)
    for i in range(5):
        t=[(0,1),(ba,bb)]
        x,y=ba,bb
        for k in range(2,K):
            x,y=(x*bb+(y-x)*ba)%M,(y*bb+x*ba)%M
            t.append((x,y))
        T.append(t)
        # advance base by K: F(K*base)
        ba,bb=(x*bb+(y-x)*ba)%M,(y*bb+x*ba)%M
    out=[]
    m=K-1
    T0,T1,T2,T3,T4=T
    for s in sys.stdin.read().split():
        n=int(s)
        a,b=T0[n&m];c,d=T1[(n>>12)&m]
        a,b=(a*d+(b-a)*c)%M,(b*d+a*c)%M
        c,d=T2[(n>>24)&m]
        a,b=(a*d+(b-a)*c)%M,(b*d+a*c)%M
        c,d=T3[(n>>36)&m]
        a,b=(a*d+(b-a)*c)%M,(b*d+a*c)%M
        c,d=T4[n>>48]
        out.append((a*d+(b-a)*c)%M)
    print("\n".join(map(str,out)))
main()
