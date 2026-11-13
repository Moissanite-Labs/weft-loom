import subprocess, time, sys

with open("expected.txt", "rb") as f:
    expected = f.read()

t0 = time.perf_counter()
p = subprocess.run([sys.executable, "wf.py"], stdin=open("input20m.txt", "rb"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
t1 = time.perf_counter()

if p.returncode != 0 or p.stdout != expected:
    print(0)
    sys.exit(0)

#Also verify a quick tie/case edge case on small input
test_in = b"Zebra apple APPLE Banana\nbanana! zebra? zebra."
p2 = subprocess.run([sys.executable, "wf.py"], input=test_in, stdout=subprocess.PIPE)
if p2.stdout != b"zebra 3\napple 2\nbanana 2\n":
    print(0)
    sys.exit(0)

elapsed = t1 - t0
# Score = MB/s on 20MB input
print(f"{20.0 / elapsed:.2f}")
