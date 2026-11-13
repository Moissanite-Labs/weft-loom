set -u
PY=~/Work/exo-live/.venv/bin/python; M=opencode-go:gemini-4-argon; E=~/Work/razi-cells/exp
go() { rm -rf $E/$1; echo "== $1 $2 start $(date +%T)"
  CELL_ARM=$2 $PY ~/Work/razi-tools/cells/colony.py $E/$1 $E/needs8v3.json --par 8 --calls 40 --steps 16 --model $M > $E/$1.log 2>&1
  echo "== $1 exit $? $(date +%T)"; }
rm -f ~/Work/razi-cells/.bench.lock
go e9t1 trynudge & go e9f1 free & go e9c1 ctrl & go e9t2 trynudge & wait
go e9f2 free & go e9t3 trynudge & go e9f3 free & go e9c2 ctrl & wait
echo ALLDONE
