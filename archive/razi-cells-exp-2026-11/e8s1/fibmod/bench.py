import subprocess
import sys
import time
import fibmod

MOD = 1_000_000_007

def ref_fib(n):
    if n == 0:
        return (0, 1)
    a, b = ref_fib(n >> 1)
    c = (a * ((b << 1) - a)) % MOD
    d = (a * a + b * b) % MOD
    if n & 1:
        return (d, (c + d) % MOD)
    return (c, d)

# Verify CLI
out = subprocess.check_output([sys.executable, "fibmod.py", "10"], text=True).strip()
if out != "55":
    print(0)
    sys.exit(0)

out_big = subprocess.check_output([sys.executable, "fibmod.py", str(10**18)], text=True).strip()
if int(out_big) != ref_fib(10**18)[0]:
    print(0)
    sys.exit(0)

# Verify function across test cases if fibmod exposes a callable or run via main/solve
# To allow fibmod.py to optimize its main/fib function, let's see how we should call it.
# Actually, if fibmod.py defines solve(n) or fib(n), we can call it, or we can test fibmod.solve(n) if present else fibmod.fib(n).
fn = getattr(fibmod, "solve", None) or getattr(fibmod, "fib_mod", None)
if fn is None:
    # check if fib returns tuple or int
    res = fibmod.fib(10)
    if isinstance(res, tuple):
        fn = lambda n: fibmod.fib(n)[0]
    else:
        fn = fibmod.fib

test_ns = [0, 1, 2, 3, 5, 10, 50, 100, 1234567, 10**12 + 39, 10**18 - 1, 10**18]
for n in test_ns:
    if fn(n) != ref_fib(n)[0]:
        print(0)
        sys.exit(0)

# Benchmark workload (~0.5s)
N_ITERS = 50000
ns = [10**18 - i * 999999999999 for i in range(500)]

t0 = time.perf_counter()
for _ in range(N_ITERS // 500):
    for n in ns:
        fn(n)
dt = time.perf_counter() - t0
print(f"{N_ITERS / dt:.1f}")
