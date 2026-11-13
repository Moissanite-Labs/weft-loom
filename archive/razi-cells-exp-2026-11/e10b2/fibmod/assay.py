import subprocess, sys, time, random
M = 10**9 + 7

def mp(n):
    # independent reference: plain 2x2 matrix power, no period reduction
    def mul(A, B):
        return [[(A[0][0]*B[0][0]+A[0][1]*B[1][0]) % M, (A[0][0]*B[0][1]+A[0][1]*B[1][1]) % M],
                [(A[1][0]*B[0][0]+A[1][1]*B[1][0]) % M, (A[1][0]*B[0][1]+A[1][1]*B[1][1]) % M]]
    R = [[1, 0], [0, 1]]; X = [[1, 1], [1, 0]]
    while n:
        if n & 1: R = mul(R, X)
        X = mul(X, X); n >>= 1
    return R[0][1]

def fail(msg):
    sys.stderr.write("FAIL " + msg + "\n")
    print(0)
    sys.exit(0)

# 1) command-line behaviour, as the need states it
for n in [0, 1, 2, 10, 10**18, 10**18 - 1, 2000000016, 123456789012345678]:
    try:
        out = subprocess.run([sys.executable, "fibmod.py", str(n)], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception as e:
        fail("cli %d %r" % (n, e))
    if out != str(mp(n)):
        fail("cli %d got %r" % (n, out))
if mp(10) != 55:
    fail("reference")

# 2) in-process correctness on random inputs, then throughput
try:
    from fibmod import fib
except Exception as e:
    fail("import %r" % (e,))
rng = random.Random(12345)
ns = [rng.randrange(10**18 + 1) for _ in range(60000)]
for n in ns[:1500]:
    if fib(n) != mp(n):
        fail("fib %d" % n)

best = float("inf")
for _ in range(5):
    t = time.perf_counter()
    for n in ns:
        fib(n)
    best = min(best, time.perf_counter() - t)
print(round(len(ns) / best))
