#!/bin/bash
# Differential test of the weft safety gate (Python, C11, JavaScript). From the repository root:
#   WEFT_CHECKOUT=/path/to/weft PYTHON=/path/to/python bash experiments/weft-threads-recheck-2026-11-15/runtime/run_diff.sh [WORKDIR]
# PYTHON needs PyTorch and NumPy; node and a C compiler (cc) must be on PATH (override with NODE, CC).
# Generated cases (about 47 MB) and raw per-case outputs go to WORKDIR (default: a new temporary folder), not into the repository.
# The last step compares the summary with the saved report.txt.
set -e
R="$(cd "$(dirname "$0")" && pwd)"
: "${WEFT_CHECKOUT:?set WEFT_CHECKOUT to the weft software checkout}"
PY="${PYTHON:-python3}"; NODE="${NODE:-node}"; CC="${CC:-cc}"
W="${1:-$(mktemp -d)}"; mkdir -p "$W"; cd "$W"
export PYTHONDONTWRITEBYTECODE=1
"$PY" "$R/gen.py" > gen.out
"$CC" -I "$WEFT_CHECKOUT/weft/runtime/invariants" "$R/cdrv.c" -o cdrv -lm
./cdrv cases_c.txt > c_out.txt
"$NODE" "$R/jsdrv.mjs" cases.jsonl js_out.jsonl --weft "$WEFT_CHECKOUT"
"$PY" "$R/run_py_and_compare.py" --weft "$WEFT_CHECKOUT" > report.txt
if cmp -s report.txt "$R/report.txt"; then echo "report.txt IDENTICAL to the saved report"; else echo "report.txt DIFFERS from the saved report"; diff report.txt "$R/report.txt" | head -20; exit 1; fi
