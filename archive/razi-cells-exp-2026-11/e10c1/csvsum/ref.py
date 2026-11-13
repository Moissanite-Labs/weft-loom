import sys, csv
from collections import defaultdict
s = defaultdict(float)
r = csv.reader(sys.stdin); next(r)
for i, c, v in r: s[c] += float(v)
for k in sorted(s): print("%s,%.2f" % (k, s[k]))
