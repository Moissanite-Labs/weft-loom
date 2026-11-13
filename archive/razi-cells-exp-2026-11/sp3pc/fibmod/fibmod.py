import sys
P=1000000007
def add(x,y):
    a,b,c=x;d,e,f=y
    return ((b*e+a*d)%P,(b*f+a*e)%P,(c*f+b*e)%P)
def main():
    data=sys.stdin.read().split()
    ns=list(map(int,data))
    T=[];s=(0,1,1)  # F(m-1),F(m),F(m+1) for m=1
    for i in range(5):
        t=[(1,0,1)];cur=(1,0,1)
        for d in range(4095):
            cur=add(cur,s);t.append(cur)
        T.append(t)
        s=add(t[4095],s)
    t0,t1,t2,t3,t4=T
    out=[]
    for n in ns:
        a,b,c=t0[n&4095]
        for t,sh in ((t1,12),(t2,24),(t3,36),(t4,48)):
            d,e,f=t[(n>>sh)&4095]
            if e or d!=1:
                a,b,c=(b*e+a*d)%P,(b*f+a*e)%P,(c*f+b*e)%P
        out.append(b)
    print("\n".join(map(str,out)))
main()
