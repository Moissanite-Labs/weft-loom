#!/bin/bash
# Runs every pair one at a time (one heavy process). Second checker.
set -u
# Usage: PYTHON=<interpreter with numpy> run_pairs.sh <real-models folder holding traces/>
P="${PYTHON:-python3}"
T="$1/traces"
cd "$(dirname "$0")/.."
run() { # A B name [opts]
  a=$1; b=$2; n=$3; shift 3
  if [ -f out/pairs/$n.json ]; then echo "skip $n"; return; fi
  $P -I scripts/matchpair.py $T/$a $a $T/$b $b $n "$@" && $P -I scripts/paircounts.py $n
}
run s135 s135i s135__s135i
run s135 s360 s135__s360
run s135 s135L s135__s135L
run s135 s135i s135__mylaund5150 --signperm out/laund/signperm_5150.npz
run s135 s135 s135__s135
run s135 s135i s135__s135i_shuf --shuffle 4242
run py py_s1 py__py_s1
run py py_s2 py__py_s2
run py_s1 py_s2 py_s1__py_s2
run py_1k py py_1k__py
run py_8k py py_8k__py
run py_32k py py_32k__py
run py falcon py__falcon
run py falcon_gate py__falcon_gate
run py s135 py__s135
run falcon s135 falcon__s135
run q08 q2 q08__q2 --block 512
echo ALLDONE
