set -u
PY=~/Work/exo-live/.venv/bin/python; E=~/Work/razi-cells/exp
go() { rm -rf $E/$1; echo "== $1 $2 start $(date +%T)"
  CELL_ARM=$2 $PY ~/Work/razi-tools/cells/colony.py $E/$1 $E/needs8v3.json --par 8 --calls 40 --steps 16 --model $3 > $E/$1.log 2>&1
  echo "== $1 exit $? $(date +%T)"; }
rm -f ~/Work/razi-cells/.bench.lock
A=anthropic:claude-fable-5-2; B=anthropic:claude-fable-5-1
go e10a1 ctrl $A & go e10b1 novar $A & go e10c1 ctrl $B & go e10d1 novar $B & wait
go e10a2 ctrl $A & go e10b2 novar $A & go e10c2 ctrl $B & go e10d2 novar $B & wait
echo ALLDONE
