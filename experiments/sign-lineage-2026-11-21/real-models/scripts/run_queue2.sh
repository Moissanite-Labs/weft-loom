#!/bin/bash
# Second queue, starts after the first: Qwen group and two exploratory controls (marked post hoc in the README).
D="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3} -I"  # PYTHON: an interpreter with torch, transformers, numpy and safetensors
cd "$D"
mkdir -p logs
# The original run waited here for run_queue.sh to finish. Run it after run_queue.sh.
pr() { n="$1__$2"; [ -f out/pairs/$n.json ] || $PY scripts/pairs.py "$D" "$@" 2>&1 | tail -1 | cut -c1-300; }
pr py s135
pr falcon s135
for k in q08 q2; do [ -f traces/$k/meta.json ] || $PY scripts/capture.py "$D" $k > logs/capture_$k.log 2>&1; tail -1 logs/capture_$k.log | cut -c1-400; done
pr q08 q2
echo QUEUE2 DONE
