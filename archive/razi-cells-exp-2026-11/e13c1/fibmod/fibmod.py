import sys
M=1000000007
K=10;B=1<<K;MASK=B-1
def fp(n):
    a,b=0,1
    for i in range(n.bit_length()-1,-1,-1):
        c=a*((2*b-a)%M)%M
        d=(a*a+b*b)%M
        if n>>i&1:
            a,b=d,(c+d)%M
        else:
            a,b=c,d
    return a,(a+b)%M if False else b
T=[]
for j in range(6):
    x,y=fp(1<<(K*j))
    # y is f_{n+1}
    t=[(0,1),(x,y)]
    a,b=x,y
    for _ in range(B-2):
        a,b=(a*y+(b-a)*x)%M,(a*x+b*y)%M
        t.append((a,b))
    T.append(t)
out=[]
for s in sys.stdin.read().split():
    n=int(s)
    a,b=0,1
    j=0
    while n:
        d=n&MASK
        if d:
            x,y=T[j][d]
            a,b=(a*y+(b-a)*x)%M,(a*x+b*y)%M
        n>>=K;j+=1
    out.append(a)
print("\n".join(map(str,out)))
