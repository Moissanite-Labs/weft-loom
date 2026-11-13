import subprocess,sys
from fibmod import fib
M=10**9+7
a,b=0,1
for i in range(5000):
    assert fib(i)==a,i
    a,b=b,(a+b)%M
# independent matrix-power check without period reduction
def mp(n):
    def mul(A,B):
        return [[(A[0][0]*B[0][0]+A[0][1]*B[1][0])%M,(A[0][0]*B[0][1]+A[0][1]*B[1][1])%M],[(A[1][0]*B[0][0]+A[1][1]*B[1][0])%M,(A[1][0]*B[0][1]+A[1][1]*B[1][1])%M]]
    R=[[1,0],[0,1]];X=[[1,1],[1,0]]
    while n:
        if n&1:R=mul(R,X)
        X=mul(X,X);n>>=1
    return R[0][1]
import random
random.seed(1)
for n in [10**18,10**18-1,2000000016,2000000015,2000000017,10**9+7,10**9+8]+[random.randrange(10**18+1) for _ in range(2000)]:
    assert fib(n)==mp(n),n
print("ok")
