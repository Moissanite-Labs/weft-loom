import sys, io, time, random
M = 1000000007
def ref(n):
    def mul(A, B):
        return ((A[0]*B[0]+A[1]*B[2]) % M, (A[0]*B[1]+A[1]*B[3]) % M,
                (A[2]*B[0]+A[3]*B[2]) % M, (A[2]*B[1]+A[3]*B[3]) % M)
    R = (1, 0, 0, 1); A = (1, 1, 1, 0)
    while n:
        if n & 1: R = mul(R, A)
        A = mul(A, A); n >>= 1
    return R[1]
random.seed(12345)
ns = [10, 1000, 10**18, 0, 1, 2] + [random.randrange(0, 10**18) for _ in range(1500)]
known = {10: 55, 1000: 517691607, 10**18: 209783453, 0: 0, 1: 1, 2: 1}
exp = [known.get(n) if n in known else ref(n) for n in ns]
src = open('fibmod.py').read()
code = compile(src, 'fibmod.py', 'exec')
old_stdout = sys.stdout
best = 0.0
ok = True
for rep in range(7):
    t0 = time.perf_counter()
    for i, n in enumerate(ns):
        sys.argv = ['fibmod.py', str(n)]
        buf = io.StringIO(); sys.stdout = buf
        try:
            exec(code, {'__name__': '__main__'})
        finally:
            sys.stdout = old_stdout
        if buf.getvalue().strip() != str(exp[i]):
            ok = False; break
    t1 = time.perf_counter()
    if not ok: break
    best = max(best, 1000.0 / (t1 - t0))
print(best if ok else 0)
