import sys
M=1000000007
P=2*(M+1)
def tab(step):
    # entries (F(k+1),F(k),F(k-1)) for k=v*step
    a=(1,1,0)  # Q^1: F2,F1,F0
    # compute Q^step
    def mul(x,y):
        return ((x[0]*y[0]+x[1]*y[1])%M,(x[0]*y[1]+x[1]*y[2])%M,(x[1]*y[1]+x[2]*y[2])%M)
    # matrix as (a,b,d) symmetric: [[a,b],[b,d]]
    r=(1,0,1);p=(1,1,0);s=step
    while s:
        if s&1:r=mul(r,p)
        p=mul(p,p);s>>=1
    t=[(1,0,1)]
    for _ in range(2047):
        t.append(mul(t[-1],r))
    return t
T0=tab(1);T1=tab(2048);T2=tab(4194304)
def main():
    out=[]
    c={}
    for tok in sys.stdin.read().split():
        v=c.get(tok)
        if v is None:
            n=int(tok)%P
            x=T0[n&2047];y=T1[(n>>11)&2047];z=T2[n>>22]
            a,b=x[0],x[1]
            # x*y
            p0=(x[0]*y[0]+x[1]*y[1])%M
            p1=(x[0]*y[1]+x[1]*y[2])%M
            p2=(x[1]*y[1]+x[2]*y[2])%M
            v=(p0*z[1]+p1*z[2])%M
            v=(p1*z[0]+p2*z[1])%M if False else v
            v=str((p1*z[0]+p2*z[1])%M)
            c[tok]=v
        out.append(v)
    print("\n".join(out))
main()
