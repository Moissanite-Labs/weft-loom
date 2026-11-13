import sys
M=10**9+7
def fib(n):
    a,b=0,1
    for ch in bin(n)[2:]:
        c=a*(2*b-a)%M
        d=(a*a+b*b)%M
        if ch=='1':
            a,b=d,(c+d)%M
        else:
            a,b=c,d
    return a
P=2*(M+1)
def main():
    out=[str(fib(int(x)%P)) for x in sys.stdin.read().split()]
    sys.stdout.write("\n".join(out)+"\n")
main()
