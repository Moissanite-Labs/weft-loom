import sys, re
from collections import Counter
c = Counter(re.findall(r'[a-z]+', sys.stdin.read().lower()))
for w, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]:
    print(w, n)
