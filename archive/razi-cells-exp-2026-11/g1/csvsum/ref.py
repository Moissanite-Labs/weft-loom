import sys, csv
from decimal import Decimal
f = sys.stdin
r = csv.reader(f)
next(r)
sums = {}
for row in r:
    if len(row) < 3:
        continue
    sums[row[1]] = sums.get(row[1], Decimal(0)) + Decimal(row[2])
for cat in sorted(sums):
    sys.stdout.write('%s,%s\n' % (cat, sums[cat].quantize(Decimal('0.01'))))
