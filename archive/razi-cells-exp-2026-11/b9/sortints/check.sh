#!/bin/sh
# prints 1e6/elapsed_seconds if output correct, else 0
export KMP_WARNINGS=0 OMP_NUM_THREADS=1
s=$(python3 -c 'import time;print(time.time())')
python3 sortints.py < data.txt > out.txt 2>/dev/null || { echo 0; exit 0; }
e=$(python3 -c 'import time;print(time.time())')
python3 -c "
import sys
a=sorted(int(x) for x in open('data.txt').read().split())
b=[int(x) for x in open('out.txt').read().split()]
ok = a==b and open('out.txt').read()=='\n'.join(map(str,a))+'\n'
print(1000000/($e-$s) if ok else 0)
" 2>/dev/null
