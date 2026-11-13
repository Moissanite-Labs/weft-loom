import sys, csv
from decimal import Decimal
r = csv.reader(sys.stdin); next(r)
d = {}
for row in r:
    if not row: continue
    d[row[1]] = d.get(row[1], Decimal(0)) + Decimal(row[2])
for k in sorted(d):
    print('%s,%.2f' % (k, d[k]))
