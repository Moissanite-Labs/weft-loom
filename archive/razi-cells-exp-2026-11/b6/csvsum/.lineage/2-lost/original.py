#!/usr/bin/env python3
import csv, sys, io
from decimal import Decimal

def main():
    data=sys.stdin.read()
    if '"' in data:
        reader=csv.reader(io.StringIO(data,newline=''))
    else:
        reader=(line.split(',') for line in io.StringIO(data,newline=None))
    header=next(reader,None)
    if header is None or [s.strip() for s in header]!=['id','cat','val']: raise ValueError('expected header id,cat,val')
    totals={}
    get=totals.get
    for _,cat,val in reader: totals[cat]=get(cat,0)+Decimal(val)
    writer=csv.writer(sys.stdout,lineterminator='\n')
    for cat in sorted(totals): writer.writerow((cat,format(totals[cat],'.2f')))
if __name__=='__main__': main()
