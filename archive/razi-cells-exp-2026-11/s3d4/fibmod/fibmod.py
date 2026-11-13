import sys
M=1000000007
P=2*(M+1)
def f(n):
    a,b=0,1
    for i in range(n.bit_length()-1,-1,-1):
        c=a*((2*b-a)%M)%M
        d=(a*a+b*b)%M
        if n>>i&1:a,b=d,(c+d)%M
        else:a,b=c,d
    return a
d=sys.stdin.read().split()
c={}
o=[]
for x in d:
    n=int(x)%P
    if n not in c:c[n]=f(n)
    o.append(c[n])
print("\n".join(map(str,o)))
