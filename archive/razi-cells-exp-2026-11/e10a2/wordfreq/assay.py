import subprocess, sys, time

exp = open('expected.txt', 'rb').read()
best = None
for _ in range(3):
    with open('data.txt', 'rb') as f:
        t = time.perf_counter()
        p = subprocess.run([sys.executable, 'wf.py'], stdin=f, stdout=subprocess.PIPE)
        dt = time.perf_counter() - t
    if p.returncode != 0 or p.stdout != exp:
        print(0)
        sys.exit(0)
    if best is None or dt < best:
        best = dt

# small edge-case check: case folding, punctuation, digits, ties by word
small = b"B a b A c C, d-e 12 c'a\n"
p = subprocess.run([sys.executable, 'wf.py'], input=small, stdout=subprocess.PIPE)
if p.stdout != b"a 3\nc 3\nb 2\nd 1\ne 1\n":
    print(0)
    sys.exit(0)

print(round(1.0 / best, 4))
