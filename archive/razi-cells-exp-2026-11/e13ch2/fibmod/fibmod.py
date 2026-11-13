import sys
M=1000000007
P=2000000016
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
def main():
    print("\n".join(str(fib(int(x))) for x in sys.stdin.read().split()))
main()
