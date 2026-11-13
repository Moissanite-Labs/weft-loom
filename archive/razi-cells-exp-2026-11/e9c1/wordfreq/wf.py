import sys, mmap
from collections import Counter

table = bytes(i + 32 if 65 <= i <= 90 else (i if 97 <= i <= 122 else 32) for i in range(256))
try:
    with mmap.mmap(0, 0, access=mmap.ACCESS_READ) as mm:
        data = mm.translate(table)
except Exception:
    data = sys.stdin.buffer.read().translate(table)
counts = Counter(data.split())
top10 = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:10]
for w, c in top10:
    print(f"{w.decode()} {c}")
