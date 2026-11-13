set -u
PY=~/Work/exo-live/.venv/bin/python
for pair in "b9 anthropic:claude-fable-5-1"; do
  set -- $pair
  rm -rf ~/Work/razi-cells/exp/$1; rm -f ~/Work/razi-cells/.bench.lock
  echo "== $1 $2 $(date)"
  $PY ~/Work/razi-tools/cells/colony.py ~/Work/razi-cells/exp/$1 ~/Work/razi-cells/exp/needs8v3.json --par 8 --calls 40 --steps 16 --model $2
  echo "== $1 exit $?"
done
