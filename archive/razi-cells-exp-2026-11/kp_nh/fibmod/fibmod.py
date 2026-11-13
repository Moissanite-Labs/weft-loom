import sys
M=10**9+7
P=2*(M+1)
C={}
def f(n):
    n%=P
    r=C.get(n)
    if r is not None: return r
    a,b=0,1
    for i in range(n.bit_length()-1,-1,-1):
        c=a*(2*b-a)%M
        d=(a*a+b*b)%M
        if n>>i&1: a,b=d,(c+d)%M
        else: a,b=c,d
    C[n]=a
    return a
sys.stdout.write("".join("%d\n"%f(int(x)) for x in sys.stdin.read().split()))
