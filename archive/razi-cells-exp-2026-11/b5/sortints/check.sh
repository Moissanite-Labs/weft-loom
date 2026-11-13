#!/bin/sh
# prints ints-per-second if correct, 0 otherwise (stderr suppressed: OMP warning "#179" polluted scores)
export KMP_WARNINGS=0
s=$(python3 -c "import time;print(time.time())")
python3 sortints.py < data.txt > out.txt 2>/dev/null || { echo 0; exit 1; }
e=$(python3 -c "import time;print(time.time())")
if cmp -s out.txt expected.txt; then python3 -c "print(1000000/($e-$s))"; else echo 0; fi
