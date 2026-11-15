#!/bin/bash
# Rerun of the probe programs of experiments/weft-threads-2026-11-15 (the "repro" folder).
#   PYTHON=/path/to/python  WEFT_CHECKOUT=/path/to/weft  bash experiments/weft-threads-recheck-2026-11-15/repro/run_all.sh
# PYTHON needs NumPy and SciPy (PyTorch as well for the three tf_splice probes). WEFT_CHECKOUT is read only by
# evaluation/skeptic_probe.py. Fresh JSON files go to out/, stdout and stderr of each run to stdout/.
# STEPS="numpy" runs only the NumPy probes (about 1.5 minutes); the default runs everything.
export PYTHONDONTWRITEBYTECODE=1
R="$(cd "$(dirname "$0")" && pwd)"
EXP="$(cd "$R/../.." && pwd)"
PY="${PYTHON:-python3}"
STEPS="${STEPS:-all}"
mkdir -p "$R/stdout" "$R/out"
: > "$R/times.txt"
t(){ n=$1; shift; s=$(date +%s); "$@" > "$R/stdout/$n.out" 2> "$R/stdout/$n.err"; rc=$?; [ -s "$R/stdout/$n.err" ] || rm -f "$R/stdout/$n.err"; e=$(date +%s); echo "$n rc=$rc sec=$((e-s))" >> "$R/times.txt"; }
cd "$R"
t e13_original $PY "$EXP/e13-geodesic-shunting-plasmid-2026-11-12/e13_geodesic_plasmid.py" --out "$R/out/e13_certificates_fresh.json" &
t e13_wireonly $PY "$EXP/weft-threads-2026-11-15/probes/e13_wireonly.py" --out "$R/out/e13-wireonly-fresh.json" &
t calibration_probe $PY probes/calibration_probe.py &
t hardening $PY probes/hardening.py &
t intersections $PY probes/intersections.py &
t donor_agreement $PY probes/donor_agreement.py &
t scale_probe $PY probes/scale_probe.py &
wait
if [ "$STEPS" != "numpy" ]; then
  t tf_splice $PY probes/tf_splice.py
  t tf_splice2 $PY probes/tf_splice2.py
  t tf_splice3 $PY probes/tf_splice3.py
  t skeptic_margins $PY evaluation/skeptic_margins.py
  t skeptic_probe $PY evaluation/skeptic_probe.py
fi
echo ALLDONE >> "$R/times.txt"
