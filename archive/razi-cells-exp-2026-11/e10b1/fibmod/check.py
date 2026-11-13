import subprocess, sys, random
from fibmod import fib
M = 1_000_000_007
# naive reference
a, b = 0, 1
ref = [0]
for i in range(5000):
    a, b = b, (a + b) % M
    ref.append(a)
for i in range(5001):
    assert fib(i) == ref[i], i
# matrix reference for large n
def mat(n):
    def mul(X, Y):
        return [[(X[0][0]*Y[0][0]+X[0][1]*Y[1][0])%M, (X[0][0]*Y[0][1]+X[0][1]*Y[1][1])%M],
                [(X[1][0]*Y[0][0]+X[1][1]*Y[1][0])%M, (X[1][0]*Y[0][1]+X[1][1]*Y[1][1])%M]]
    R = [[1,0],[0,1]]; B = [[1,1],[1,0]]
    while n:
        if n & 1: R = mul(R, B)
        B = mul(B, B); n >>= 1
    return R[0][1]
random.seed(1)
for _ in range(2000):
    n = random.randrange(10**18 + 1)
    assert fib(n) == mat(n), n
assert fib(10**18) == mat(10**18)
out = subprocess.run([sys.executable, 'fibmod.py', '10'], capture_output=True, text=True).stdout.strip()
assert out == '55', out
out = subprocess.run([sys.executable, 'fibmod.py', str(10**18)], capture_output=True, text=True).stdout.strip()
assert out == str(mat(10**18)), out
print('OK', fib(10**18))
