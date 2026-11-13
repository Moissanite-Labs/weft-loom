import sys,csv
from collections import defaultdict
from decimal import Decimal
s=defaultdict(Decimal)
r=csv.reader(sys.stdin); next(r)
for i,c,v in r: s[c]+=Decimal(v)
for k in sorted(s): print('%s,%.2f'%(k,s[k]))
