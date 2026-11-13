import sys
M=1000000007
def fib(n):
    a,b=0,1
    for i in range(n.bit_length()-1,-1,-1):
        c=a*((2*b-a)%M)%M
        d=(a*a+b*b)%M
        if n>>i&1:
            a,b=d,(c+d)%M
        else:
            a,b=c,d
    return a
# fast: pisano period of 1e9+7 divides 2(p+1) or p-1; reduce n
P=2*(M+1)*(M-1)
out=[]
for l in sys.stdin.read().split():
    out.append(fib(int(l)%P))
print("\n".join(map(str,out)))
