import sys
M=1000000007
def f(n):
    a,b=0,1
    for i in range(n.bit_length()-1,-1,-1):
        c=a*((2*b-a)%M)%M
        d=(a*a+b*b)%M
        if n>>i&1:a,b=d,(c+d)%M
        else:a,b=c,d
    return a
c={}
o=[]
for l in sys.stdin.read().split():
    n=int(l)
    r=c.get(n)
    if r is None:r=c[n]=f(n)
    o.append(r)
print("\n".join(map(str,o)))
