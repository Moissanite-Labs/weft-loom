#!/bin/bash
# Runs check_exact_mine.py under three interpreter modes and compares outputs byte for byte.
cd "$(dirname "$0")"
O=../out
python3 -I -B check_exact_mine.py > $O/exact_mode1.txt; e1=$?
python3 -I -O -B check_exact_mine.py > $O/exact_mode2.txt; e2=$?
python3 -I -B -W error check_exact_mine.py > $O/exact_mode3.txt; e3=$?
if cmp -s $O/exact_mode1.txt $O/exact_mode2.txt && cmp -s $O/exact_mode1.txt $O/exact_mode3.txt; then same=identical; else same=DIFFER; fi
echo "exits $e1 $e2 $e3; outputs $same; python3 $(python3 -c 'import sys;print(sys.version.split()[0])')" > $O/exact_parity.txt
cat $O/exact_mode1.txt $O/exact_parity.txt
