#!/bin/sh
# Runs every exact script under the three required interpreter modes and checks
# that stdout is byte-identical across modes. Exit 1 on any failure or mismatch.
set -u
cd "$(dirname "$0")" || exit 1
status=0
for s in exact_null.py check_independent.py symmetry_exact.py site_sentence.py; do
  python3 -I -B "$s" > "../out/.parity_a_$s.txt" 2>&1 || { echo "FAIL -I -B $s"; status=1; }
  python3 -I -O -B "$s" > "../out/.parity_b_$s.txt" 2>&1 || { echo "FAIL -I -O -B $s"; status=1; }
  python3 -I -B -W error "$s" > "../out/.parity_c_$s.txt" 2>&1 || { echo "FAIL -W error $s"; status=1; }
  if cmp -s "../out/.parity_a_$s.txt" "../out/.parity_b_$s.txt" && cmp -s "../out/.parity_a_$s.txt" "../out/.parity_c_$s.txt"; then
    echo "PARITY OK $s ($(wc -l < "../out/.parity_a_$s.txt" | tr -d ' ') lines)"
  else
    echo "PARITY MISMATCH $s"; status=1
  fi
done
exit $status
