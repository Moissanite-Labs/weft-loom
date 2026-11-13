import os
import random
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
if not os.path.exists('input.txt'):
    rng = random.Random(831927)
    values = [rng.randrange(-10**9, 10**9) for _ in range(1_000_000)]
    with open('input.txt', 'wb') as f:
        f.write((' '.join(map(str, values)) + '\n').encode())
    with open('expected.txt', 'wb') as f:
        f.write(('\n'.join(map(str, sorted(values))) + '\n').encode())

cases = [b'', b' \t\n\r\v\f', b'4 -1 0 4 +2 -0003', b'9\t7\r\n-6\v0\f+9', b'10000000000000000000000000000000000000000000000000000000000000000 -999999999999999999999999999999999999999999999999999999999999999999999 1', b'0 -0 +0 00']
for data in cases:
    expected = ''.join(str(n) + '\n' for n in sorted(map(int, data.split()))).encode()
    p = subprocess.run([sys.executable, 'sortints.py'], input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode or p.stdout != expected:
        print(0)
        sys.exit(0)
expected = open('expected.txt', 'rb').read()
times = []
for _ in range(3):
    with open('input.txt', 'rb') as f:
        start = time.perf_counter()
        p = subprocess.run([sys.executable, 'sortints.py'], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        times.append(time.perf_counter() - start)
    if p.returncode or p.stdout != expected:
        print(0)
        sys.exit(0)
print(3 / sum(times))
