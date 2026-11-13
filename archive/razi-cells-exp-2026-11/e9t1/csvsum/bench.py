import subprocess, time, sys

t0 = time.perf_counter()
with open("test.csv", "rb") as f:
    res = subprocess.run([sys.executable, "csvsum.py"], stdin=f, capture_output=True)
dt = time.perf_counter() - t0

if res.returncode != 0:
    print(0)
    sys.exit(1)

with open("expected.txt", "rb") as f:
    exp = f.read().splitlines()

got = res.stdout.splitlines()
if len(got) != len(exp):
    print(0)
    sys.exit(1)

for g, e in zip(got, exp):
    gc, gv = g.split(b",")
    ec, ev = e.split(b",")
    if gc != ec or abs(float(gv) - float(ev)) > 0.05:
        print(0)
        sys.exit(1)

# rows per second
print(f"{2000000.0 / dt:.1f}")
