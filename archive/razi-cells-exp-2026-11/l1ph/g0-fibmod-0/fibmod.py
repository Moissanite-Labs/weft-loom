import sys
M=10**9+7
def f(n):
    a,b=0,1
    for c in bin(n)[2:]:
        t=(a*(2*b-a))%M
        u=(a*a+b*b)%M
        if c=='1':
            a,b=u,(t+u)%M
        else:
            a,b=t,u
    return a
sys.stdout.write('\n'.join([str(f(int(x))) for x in sys.stdin.read().split()])+'\n')
