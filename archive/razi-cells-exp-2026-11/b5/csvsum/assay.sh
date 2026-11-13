#!/bin/sh
s=$(python3 -c 'import time;print(time.time())')
python3 csvsum.py < data.csv > out.txt || exit 1
e=$(python3 -c 'import time;print(time.time())')
cmp -s out.txt ref.txt || { echo 0; exit 0; }
python3 -c "print(round(10000/(($e-$s)*1000),3))"
