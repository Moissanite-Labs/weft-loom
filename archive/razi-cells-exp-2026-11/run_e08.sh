set -u
PY=~/Work/exo-live/.venv/bin/python; M=opencode-go:gemini-4-argon; E=~/Work/razi-cells/exp
go() { rm -rf $E/$1; echo "== $1 $2 start $(date +%T)"
  CELL_ARM=$2 $PY ~/Work/razi-tools/cells/colony.py $E/$1 $E/needs8v3.json --par 8 --calls 40 --steps 16 --model $M > $E/$1.log 2>&1
  echo "== $1 exit $? $(date +%T)"; }
rm -f ~/Work/razi-cells/.bench.lock
go e8c1 ctrl & go e8n1 novar & go e8s1 safebold & go e8n2 novar & wait
go e8s2 safebold & go e8n3 novar & go e8s3 safebold & wait
echo ALLDONE
