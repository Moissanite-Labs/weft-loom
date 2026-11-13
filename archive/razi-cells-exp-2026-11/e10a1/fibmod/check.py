import subprocess, sys
M=1_000_000_007
def naive(n):
    a,b=0,1
    for _ in range(n): a,b=b,(a+b)%M
    return a
def mat(n):
    def mul(A,B):
        return [[(A[0][0]*B[0][0]+A[0][1]*B[1][0])%M,(A[0][0]*B[0][1]+A[0][1]*B[1][1])%M],[(A[1][0]*B[0][0]+A[1][1]*B[1][0])%M,(A[1][0]*B[0][1]+A[1][1]*B[1][1])%M]]
    R=[[1,0],[0,1]];P=[[1,1],[1,0]]
    while n:
        if n&1:R=mul(R,P)
        P=mul(P,P);n>>=1
    return R[0][1]
sys.path.insert(0,'.')
import fibmod
for n in list(range(0,300))+[10**18,10**18-1,123456789012345678,2**59,999999999999]:
    exp = naive(n) if n<300 else mat(n)
    assert mat(n)==exp
    assert fibmod.fib(n)==exp,(n,)
for n in [0,1,10,10**18]:
    out=subprocess.run([sys.executable,'fibmod.py',str(n)],capture_output=True,text=True).stdout.strip()
    assert out==str(mat(n)),(n,out)
print("OK", fibmod.fib(10), fibmod.fib(10**18))
