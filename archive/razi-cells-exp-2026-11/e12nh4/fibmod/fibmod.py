import sys
M=1000000007
T=[(0,1)]
_a,_b=0,1
for _ in range(65536):
    _a,_b=_b,(_a+_b)%M
    T.append((_a,_b))
def fib(n):
    L=n.bit_length()
    if L<=16: return T[n][0]
    s=L-16
    a,b=T[n>>s]
    while s:
        s-=1
        t=a*((2*b-a)%M)%M
        u=(a*a+b*b)%M
        if (n>>s)&1: a,b=u,(t+u)%M
        else: a,b=t,u
    return a
if __name__=="__main__":
    print(fib(int(sys.argv[1])))
