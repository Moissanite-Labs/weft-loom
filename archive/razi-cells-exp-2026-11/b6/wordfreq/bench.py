import collections
import pathlib
import random
import re
import statistics
import subprocess
import sys
import time

root = pathlib.Path(__file__).parent
fixture = root / 'input.txt'
expected_file = root / 'expected.txt'

def reference(text):
    counts = collections.Counter(re.findall('[a-z]+', text.lower()))
    return ''.join(f'{w} {n}\n' for w, n in sorted(counts.items(), key=lambda p: (-p[1], p[0]))[:10]).encode()

if not fixture.exists():
    rng = random.Random(4721)
    vocabulary = ['the', 'of', 'and', 'to', 'a', 'in', 'is', 'it', 'you', 'that', 'with', 'as', 'for', 'was', 'on', 'are']
    vocabulary += [''.join(rng.choices('abcdefghijklmnopqrstuvwxyz', k=rng.randrange(3, 15))) for _ in range(12000)]
    chunks = []
    length = 0
    while length < 20_000_000:
        words = rng.choices(vocabulary[:16], k=700) + rng.choices(vocabulary[16:], k=300)
        rng.shuffle(words)
        chunk = ''.join((w.upper() if rng.random() < .2 else w) + rng.choice([' ', ' ', '\n', ', ', '. ', '\t', '123', "'"]) for w in words)
        chunks.append(chunk)
        length += len(chunk)
    text = ''.join(chunks)[:20_000_000]
    fixture.write_text(text)
    expected_file.write_bytes(reference(text))

cases = ['', 'Hello hello WORLD world world!', 'z a b z a b', 'One_one 123two--THREE\nthree', ' '.join('abcdefghijklmnop'), 'Éclair İ Aß Z9z', 'x'*100000 + ' Z z']
for text in cases:
    result = subprocess.run([sys.executable, str(root / 'wf.py')], input=text.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode or result.stdout != reference(text):
        print(0)
        sys.exit(0)

times = []
for _ in range(2):
    with fixture.open('rb') as source:
        start = time.perf_counter()
        result = subprocess.run([sys.executable, str(root / 'wf.py')], stdin=source, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        times.append(time.perf_counter() - start)
    if result.returncode or result.stdout != expected_file.read_bytes():
        print(0)
        sys.exit(0)
print(1 / statistics.mean(times))
