import csv,sys
from decimal import Decimal
d={}
r=csv.DictReader(open('data.csv'))
for row in r:
    d[row['cat']]=d.get(row['cat'],Decimal(0))+Decimal(row['val'])
for k in sorted(d): print('%s %.2f'%(k,d[k]))
