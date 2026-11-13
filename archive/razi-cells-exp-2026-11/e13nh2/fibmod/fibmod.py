import sys
M=1000000007
P=2*(M+1)
def fib(n):
    a,b=0,1
    for i in range(n.bit_length()-1,-1,-1):
        c=a*(2*b-a)%M
        d=(a*a+b*b)%M
        if n>>i&1:
            a,b=d,(c+d)%M
        else:
            a,b=c,d
    return a
def main():
    cache={}
    out=[]
    for x in sys.stdin.read().split():
        n=int(x)%P
        r=cache.get(n)
        if r is None:
            r=cache[n]=str(fib(n))
        out.append(r)
    print("\n".join(out))
main()
