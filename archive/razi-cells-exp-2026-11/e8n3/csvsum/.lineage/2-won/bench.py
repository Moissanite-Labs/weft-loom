import subprocess, time, sys

with open("expected.txt", "rb") as f:
    expected = f.read()

t0 = time.perf_counter()
with open("data.csv", "rb") as fin:
    p = subprocess.run([sys.executable, "csvsum.py"], stdin=fin, capture_output=True)
dt = time.perf_counter() - t0

if p.returncode != 0 or p.stdout != expected:
    print("0")
    sys.exit(1)

# Score = rows per second (in millions) or 1000 / dt
print(f"{2000000.0 / dt:.2f}")
