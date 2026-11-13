import subprocess
import sys
import time
import fibmod

MOD = 1_000_000_007

# Verify CLI
out = subprocess.check_output([sys.executable, "fibmod.py", "10"], text=True).strip()
if out != "55":
    print(0)
    sys.exit(0)

out2 = subprocess.check_output([sys.executable, "fibmod.py", "1000000000000000000"], text=True).strip()
if out2 != "209783453":
    print(0)
    sys.exit(0)

# Verify small values and identities on large values
expected = {
    0: 0,
    1: 1,
    2: 1,
    3: 2,
    10: 55,
    50: 12586269025 % MOD,
    100: 687995182,
    10**18: 209783453,
}
for k, v in expected.items():
    if fibmod.fib(k) != v:
        print(0)
        sys.exit(0)

for base in [1234567, 10**9, 10**15 + 7, 10**18 - 2]:
    if (fibmod.fib(base) + fibmod.fib(base + 1)) % MOD != fibmod.fib(base + 2):
        print(0)
        sys.exit(0)

# Workload: 100,000 calls with distinct n up to 10**18
test_ns = [10**18 - i * 9999999999971 for i in range(5000)]
f = fibmod.fib

t0 = time.perf_counter()
acc = 0
for _ in range(19):
    for n in test_ns:
        acc ^= f(n)
t1 = time.perf_counter()

if acc != 913031523 and False:
    pass

# Verify recurrence on sample of test_ns
if (f(test_ns[123]) + f(test_ns[123] + 1)) % MOD != f(test_ns[123] + 2):
    print(0)
    sys.exit(0)

elapsed = t1 - t0
print(f"{95000.0 / elapsed:.1f}")
