#!/bin/bash
# Sequential queue: one heavy process at a time.
D="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3} -I"  # PYTHON: an interpreter with torch, transformers, numpy and safetensors
cd "$D"
cap() { [ -f traces/$1/meta.json ] || $PY scripts/capture.py "$D" $1 2>&1 | grep -v "Loading\|NOTE\|Warning" | tail -2; }
pr() { n="$1__$2${3:+_$3}"; [ -f out/pairs/$n.json ] || $PY scripts/pairs.py "$D" "$@" 2>&1 | tail -2 | cut -c1-400; }
for k in py py_s1 py_s2 py_1k py_8k py_32k; do cap $k; done
pr s135 s135
pr s135 s360
pr s135 s135L
pr py py_s1
pr py py_s2
pr py_s1 py_s2
pr py_1k py
pr py_8k py
pr py_32k py
# The original run waited here for the Falcon download to finish. Run download.py first instead.
cap falcon
pr py falcon
pr py falcon_gate
$PY scripts/pairs.py "$D" s135 s135i --shuffle 4242 --name s135__s135i_shuf 2>&1 | tail -1 | cut -c1-400
echo QUEUE DONE
