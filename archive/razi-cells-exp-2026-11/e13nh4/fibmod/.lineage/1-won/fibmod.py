import sys
M=10**9+7
P=2000000016
def fib(n):
    a,b=0,1
    for i in range(n.bit_length()-1,-1,-1):
        c=a*(2*b-a)%M
        d=(a*a+b*b)%M
        if n>>i&1:a,b=d,(c+d)%M
        else:a,b=c,d
    return a
cache={}
out=[]
for x in sys.stdin.read().split():
    n=int(x)%P
    r=cache.get(n)
    if r is None:
        r=cache[n]=fib(n)
    out.append(r)
print("\n".join(map(str,out)))
