import subprocess, sys, time, random
M = 1000000007
# correctness via CLI
out = subprocess.run([sys.executable, "fibmod.py", "10"], capture_output=True, text=True).stdout.strip()
if out != "55": print(0); sys.exit(0)
out = subprocess.run([sys.executable, "fibmod.py", "1000000000000000000"], capture_output=True, text=True).stdout.strip()
if out != "209783453": print(0); sys.exit(0)
import fibmod
def slow(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, (a + b) % M
    return a
random.seed(1)
for n in [0, 1, 2, 3, 100, 1234, 99999] + [random.randrange(2000) for _ in range(20)]:
    if fibmod.fib(n) != slow(n): print(0); sys.exit(0)
ns = [random.randrange(10**18) for _ in range(20000)]
f = fibmod.fib
t = time.perf_counter()
for n in ns: f(n)
dt = time.perf_counter() - t
print(int(len(ns) / dt))
