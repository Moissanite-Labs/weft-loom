import subprocess, sys, time

small_expected = [2, -1, 8, 1, -1]
for i, exp in enumerate(small_expected):
    with open(f"small_{i}.txt", "rb") as f:
        data = f.read()
    res = subprocess.run([sys.executable, "maze.py"], input=data, capture_output=True)
    if res.returncode != 0 or int(res.stdout.strip()) != exp:
        print(0)
        sys.exit(0)

with open("expected.txt") as f:
    exp2000, exp_unreach = [int(x) for x in f.read().split()]

with open("maze2000.txt", "rb") as f:
    m1 = f.read()
with open("maze2000_unreach.txt", "rb") as f:
    m2 = f.read()

t0 = time.perf_counter()
r1 = subprocess.run([sys.executable, "maze.py"], input=m1, capture_output=True)
r2 = subprocess.run([sys.executable, "maze.py"], input=m2, capture_output=True)
r3 = subprocess.run([sys.executable, "maze.py"], input=m1, capture_output=True)
t1 = time.perf_counter()

if (r1.returncode != 0 or int(r1.stdout.strip()) != exp2000 or
    r2.returncode != 0 or int(r2.stdout.strip()) != exp_unreach or
    r3.returncode != 0 or int(r3.stdout.strip()) != exp2000):
    print(0)
    sys.exit(0)

elapsed = t1 - t0
print(f"{100.0 / elapsed:.2f}")
