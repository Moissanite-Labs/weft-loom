import random, subprocess, sys
from fibmod import fib_mod

MOD = 1_000_000_007

# naive
naive = [0, 1]
for i in range(2, 300):
    naive.append((naive[-1] + naive[-2]) % MOD)
for i in range(300):
    assert fib_mod(i) == naive[i], i

# matrix exponentiation cross-check for large n
def mat_mul(A, B):
    return (
        (A[0]*B[0] + A[1]*B[2]) % MOD,
        (A[0]*B[1] + A[1]*B[3]) % MOD,
        (A[2]*B[0] + A[3]*B[2]) % MOD,
        (A[2]*B[1] + A[3]*B[3]) % MOD,
    )

def fib_matrix(n):
    r = (1,0,0,1)
    m = (1,1,1,0)
    while n:
        if n & 1:
            r = mat_mul(r, m)
        m = mat_mul(m, m)
        n >>= 1
    return r[1]

for _ in range(20):
    n = random.randrange(0, 10**18)
    assert fib_mod(n) == fib_matrix(n), n

# edge cases via subprocess CLI
for n, exp in [('0','0'), ('1','1'), ('2','1'), ('10','55')]:
    out = subprocess.check_output([sys.executable, 'fibmod.py', n]).decode().strip()
    assert out == exp, (n, out, exp)

print('OK')
