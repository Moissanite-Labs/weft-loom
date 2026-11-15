#!/bin/bash
# usage: run_var.sh LABEL WORKTREE_PATH   (env flags set by caller; PYTHON=/path/to/python, default python3)
# WORKTREE_PATH is a checkout of the head of weft PR 206 (see the commands that recreate it).
# Writes ctrl/out_LABEL.json (and ctrl/err_LABEL.txt) next to this script; prints the summary per regime.
D="$(cd "$(dirname "$0")" && pwd)"
WT="$2"
PY="${PYTHON:-python3}"
PYTHONPATH="$WT" $PY "$D/e15_var.py" --out "$D/out_$1.json" >/dev/null 2>"$D/err_$1.txt" || cat "$D/err_$1.txt" | tail -3
$PY - <<P
import json
d=json.load(open('$D/out_$1.json'))
print('$1')
for m,s in d['summary_by_regime'].items():
    print(' ',m[:12].ljust(12),'pass',s['passes_of_12'],'R2',s['mean_shifted_ood_r2'],'minR2',s['mean_min_wave_r2'],'ood',s['mean_max_ood_tail_ratio'],'poison',s['total_poison_committed_of_120'])
P
