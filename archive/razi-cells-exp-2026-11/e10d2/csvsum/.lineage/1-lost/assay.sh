#!/bin/sh
# Prints rows/sec (in thousands), best of 3 runs, if output matches reference, else 0.
cd "$(dirname "$0")" 2>/dev/null
[ -f data.csv ] || python3 gen.py 2000000 > data.csv
[ -f ref.txt ] || python3 -c "
import csv,sys
from collections import defaultdict
s=defaultdict(float)
r=csv.reader(open('data.csv')); next(r)
for i,c,v in r: s[c]+=float(v)
for c in sorted(s): print('%s,%.2f'%(c,s[c]))
" > ref.txt
python3 - <<'EOF'
import subprocess, time, sys
ref=open('ref.txt','rb').read()
best=None
for _ in range(3):
    t=time.time()
    p=subprocess.run(['python3','csvsum.py'],stdin=open('data.csv','rb'),capture_output=True)
    dt=time.time()-t
    if p.returncode!=0 or p.stdout!=ref:
        print(0); sys.exit(0)
    best=dt if best is None else min(best,dt)
print(round(2000/best,1))
EOF
