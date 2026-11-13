import sys
M=1000000007
P=2*(M+1)
def fib(n):
    a,b=0,1
    for c in bin(n%P)[2:]:
        t=a*(2*b-a)%M
        u=(a*a+b*b)%M
        if c=='1':
            a,b=u,(t+u)%M
        else:
            a,b=t,u
    return a
print("\n".join([str(fib(int(x))) for x in sys.stdin.read().split()]))
