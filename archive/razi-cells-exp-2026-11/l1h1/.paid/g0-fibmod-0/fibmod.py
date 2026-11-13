import sys
M=1000000007
def mul(X,Y):
    a,b,c,d=X; e,f,g,h=Y
    return ((a*e+b*g)%M,(a*f+b*h)%M,(c*e+d*g)%M,(c*f+d*h)%M)
I=(1,0,0,1)
Q=(1,1,1,0)
W=11
S=1<<W
MASK=S-1
NW=(60+W-1)//W
tables=[]
P=Q
for k in range(NW):
    T=[I]*S
    x=I
    for j in range(1,S):
        x=mul(x,P)
        T[j]=x
    tables.append(T)
    P=mul(x,P)
def f(n):
    r=I
    k=0
    while n:
        d=n&MASK
        if d:
            r=mul(r,tables[k][d])
        n>>=W
        k+=1
    return r[1]
def main():
    out=[]
    cache={}
    for t in sys.stdin.read().split():
        n=int(t)
        r=cache.get(n)
        if r is None:
            r=cache[n]=f(n)
        out.append(r)
    print("\n".join(map(str,out)))
main()
