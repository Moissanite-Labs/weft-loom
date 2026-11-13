import sys, time, random, subprocess
sys.path.insert(0, '.')
import fibmod
M = 1_000_000_007

def ref(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a % M

# correctness: small values vs naive, plus known large value, plus CLI
for n in list(range(0, 200)) + [1000, 5000]:
    if fibmod.fib(n) != ref(n):
        print(0); sys.exit(0)
if fibmod.fib(10**18) != 209783453:
    print(0); sys.exit(0)
out = subprocess.run([sys.executable, 'fibmod.py', '10'], capture_output=True, text=True).stdout.strip()
if out != '55':
    print(0); sys.exit(0)

random.seed(12345)
ns = [random.randrange(1, 10**18) for _ in range(20000)]
t = time.perf_counter()
s = 0
for n in ns:
    s ^= fibmod.fib(n)
dt = time.perf_counter() - t
print(len(ns) / dt)
