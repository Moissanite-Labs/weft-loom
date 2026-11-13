import subprocess
import time
import hashlib
import sys

with open('expected.txt', 'rb') as f:
    expected_hash = hashlib.md5(f.read()).digest()

with open('input.txt', 'rb') as f:
    input_data = f.read()

t0 = time.perf_counter()
p = subprocess.run([sys.executable, 'sortints.py'], input=input_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
t1 = time.perf_counter()

if p.returncode != 0:
    print(0)
    sys.exit(0)

if hashlib.md5(p.stdout).digest() != expected_hash:
    print(0)
    sys.exit(0)

elapsed = t1 - t0
# Print score: items per millisecond (1000 / elapsed)
print(f"{1000.0 / elapsed:.2f}")
