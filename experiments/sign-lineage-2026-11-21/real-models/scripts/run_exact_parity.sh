#!/bin/bash
# Run the exact checker under three interpreter modes; outputs must be byte-identical.
D="$(cd "$(dirname "$0")/.." && pwd)"
set -u
i=0
for mode in "-I -B" "-I -O -B" "-I -B -W error"; do
  i=$((i+1))
  python3 $mode "$D/scripts/check_exact.py" > "$D/out/check_exact_mode$i.txt" 2>&1
  echo "mode '$mode' exit $?"
done
if cmp -s "$D/out/check_exact_mode1.txt" "$D/out/check_exact_mode2.txt" && cmp -s "$D/out/check_exact_mode1.txt" "$D/out/check_exact_mode3.txt"; then echo "outputs byte-identical"; else echo "outputs DIFFER"; exit 1; fi
