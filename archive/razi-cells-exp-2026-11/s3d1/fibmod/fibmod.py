import sys
M=1000000007
def fib(n):
    a,b=0,1
    for c in bin(n)[2:]:
        t=a*(2*b-a)%M
        u=(a*a+b*b)%M
        if c=='1':
            a,b=u,(t+u)%M
        else:
            a,b=t,u
    return a
def main():
    d=sys.stdin.read().split()
    sys.stdout.write("\n".join(str(fib(int(x))) for x in d)+("\n" if d else ""))
main()
