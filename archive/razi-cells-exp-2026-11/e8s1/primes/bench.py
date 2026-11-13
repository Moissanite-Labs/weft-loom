import subprocess
import sys
import time

EXPECTED = {
    -5: 0,
    0: 0,
    1: 0,
    2: 0,
    3: 1,
    4: 2,
    5: 2,
    6: 3,
    7: 3,
    8: 4,
    10: 4,
    11: 4,
    12: 5,
    13: 5,
    14: 6,
    100: 25,
    1000: 168,
    10000: 1229,
    100000: 9592,
    1000000: 78498,
    5000000: 348513,
    10000000: 664579,
    25000000: 1565927,
}

# Verify CLI correctness first
for n in [0, 1, 2, 3, 4, 5, 10, 100, 5000000]:
    out = subprocess.check_output([sys.executable, "primes.py", str(n)], stderr=subprocess.STDOUT).decode().strip()
    if int(out) != EXPECTED[n]:
        print(0)
        sys.exit(0)

# Verify in-process across all expected values and benchmark
# Run primes.py via runpy or exec on sys.argv[1] or by calling its main logic
with open("primes.py", "rb") as f:
    code = compile(f.read(), "primes.py", "exec")

def run_inproc(n_str):
    import io
    old_argv = sys.argv
    old_stdout = sys.stdout
    sys.argv = ["primes.py", n_str]
    buf = io.StringIO()
    sys.stdout = buf
    try:
        exec(code, {"__name__": "__main__"})
    finally:
        sys.stdout = old_stdout
        sys.argv = old_argv
    return int(buf.getvalue().strip())

for n, exp in EXPECTED.items():
    if run_inproc(str(n)) != exp:
        print(0)
        sys.exit(0)

# Benchmark: mix of 5,000,000 and 25,000,000 in-process + CLI 5,000,000
t0 = time.perf_counter()
for _ in range(15):
    if run_inproc("5000000") != 348513:
        print(0)
        sys.exit(0)
for _ in range(5):
    if run_inproc("25000000") != 1565927:
        print(0)
        sys.exit(0)
for _ in range(3):
    out = subprocess.check_output([sys.executable, "primes.py", "5000000"]).decode().strip()
    if int(out) != 348513:
        print(0)
        sys.exit(0)
elapsed = time.perf_counter() - t0
# Score: operations per second
print(f"{100.0 / elapsed:.2f}")
