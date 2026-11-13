import sys,csv
from decimal import Decimal
from collections import defaultdict
r=csv.reader(sys.stdin); next(r)
s=defaultdict(Decimal)
for i,c,v in r: s[c]+=Decimal(v)
for k in sorted(s): print("%s,%.2f"%(k,s[k]))
