#!/bin/bash
# Run the exact scripts under the three interpreter modes and compare outputs byte for byte.
cd "$(dirname "$0")"
# Optional argument: the folder of the derivation scripts checked black-box (default ../../scripts).
THEIRS="${1:-$(cd ../../scripts && pwd)}"
for s in exact_refute.py tie_search.py "blackbox_their_null.py $THEIRS"; do
  h1=$(python3 -I -B $s | shasum -a 256); e1=${PIPESTATUS[0]}
  h2=$(python3 -I -O -B $s | shasum -a 256); e2=${PIPESTATUS[0]}
  h3=$(python3 -I -B -W error $s | shasum -a 256); e3=${PIPESTATUS[0]}
  if [ "$h1" == "$h2" ] && [ "$h1" == "$h3" ]; then same=identical; else same=DIFFER; fi
  echo "${s%% *}: exits $e1 $e2 $e3, outputs $same"
done
python3 -I -B exact_refute.py > ../out/exact_refute.txt
