import sys
from collections import Counter
data = sys.stdin.buffer.read().decode('utf-8', 'replace')
# split on non-alphabetic? use regex on ascii letters after lower
import re
words = re.findall(r'[a-z]+', data.lower())
c = Counter(words)
top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
print("\n".join("%s %d" % kv for kv in top))
