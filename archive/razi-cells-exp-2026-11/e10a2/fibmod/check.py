import subprocess, sys
from fibmod import fib
M=1000000007
# naive check
a,b=0,1
for i in range(2000):
    assert fib(i)==a, i
    a,b=b,(a+b)%M
# matrix check for big n
def mat(n):
    def mul(A,B):
        return [[(A[0][0]*B[0][0]+A[0][1]*B[1][0])%M,(A[0][0]*B[0][1]+A[0][1]*B[1][1])%M],
                [(A[1][0]*B[0][0]+A[1][1]*B[1][0])%M,(A[1][0]*B[0][1]+A[1][1]*B[1][1])%M]]
    R=[[1,0],[0,1]];P=[[1,1],[1,0]]
    while n:
        if n&1:R=mul(R,P)
        P=mul(P,P);n>>=1
    return R[0][1]
import random
random.seed(1)
for _ in range(2000):
    n=random.randrange(10**18+1)
    assert fib(n)==mat(n), n
assert fib(10**18)==mat(10**18)
print("ok", fib(10), fib(10**18))
