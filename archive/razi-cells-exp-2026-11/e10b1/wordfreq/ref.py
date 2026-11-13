import sys, re
counts = {}
for line in sys.stdin:
    for w in re.findall(r"[a-z]+", line.lower()):
        counts[w] = counts.get(w, 0) + 1
for w, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]:
    print(w, n)
