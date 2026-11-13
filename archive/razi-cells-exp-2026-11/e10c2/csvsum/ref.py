import sys, csv
from collections import defaultdict
r = csv.reader(sys.stdin); next(r)
s = defaultdict(float)
for row in r: s[row[1]] += float(row[2])
for k in sorted(s): print("%s,%.2f" % (k, s[k]))
