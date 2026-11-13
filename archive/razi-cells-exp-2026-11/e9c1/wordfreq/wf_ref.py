import sys, re
from collections import Counter

words = re.findall(r'[a-z]+', sys.stdin.read().lower())
counts = Counter(words)
top10 = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:10]
for w, c in top10:
    print(f"{w} {c}")
