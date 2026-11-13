import sys, csv
from decimal import Decimal
from collections import defaultdict
d = defaultdict(Decimal)
rd = csv.reader(sys.stdin)
next(rd)
for row in rd:
    if row:
        d[row[1]] += Decimal(row[2])
for k in sorted(d):
    print('%s,%.2f' % (k, d[k]))
