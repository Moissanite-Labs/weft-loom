import subprocess, sys, time

exp = open('expected.txt', 'rb').read()
data = open('data.txt', 'rb').read()
times = []
for _ in range(5):
    t = time.perf_counter()
    p = subprocess.run([sys.executable, 'sortints.py'], input=data,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    dt = time.perf_counter() - t
    if p.returncode != 0 or p.stdout != exp:
        print(0)
        sys.exit(0)
    times.append(dt)
# small edge cases: empty input, negatives, mixed whitespace
for inp, want in ((b'', b''), (b'3 -1\n2\t10  -7\n', b'-7\n-1\n2\n3\n10\n')):
    p = subprocess.run([sys.executable, 'sortints.py'], input=inp,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if p.returncode != 0 or p.stdout != want:
        print(0)
        sys.exit(0)
times.sort()
# score: runs per second, median of 5
print(round(1.0 / times[2], 4))
