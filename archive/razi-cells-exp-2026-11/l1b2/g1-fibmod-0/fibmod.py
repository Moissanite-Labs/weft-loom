import sys
M=1000000007
P=2*(M+1)
def f(n):
    a=0;b=1
    for c in bin(n%P)[2:]:
        t=b*b
        x=a*(2*b-a)%M
        y=(a*a+t)%M
        if c=='1':
            a=y;b=(x+y)%M
        else:
            a=x;b=y
    return a
def main():
    d=sys.stdin.read().split()
    sys.stdout.write("\n".join([str(f(int(s))) for s in d])+"\n")
main()
