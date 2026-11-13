#!/bin/sh
# E12: ctrl, novar, ctrl+hold, novar+hold on Sonnet 5.5, cheap protocol, 4 interleaved reps. Usage: run_e12.sh pilot|full
E=$HOME/Work/razi-cells/exp; M=anthropic:claude-sonnet-5-5
if [ "$1" = pilot ]; then CELL_HOLD=1 sh $E/run_cheap.sh $E/e12p $M novar; exit $?; fi
for i in 1 2 3 4; do
  CELL_HOLD= sh $E/run_cheap.sh $E/e12c$i $M ctrl || echo "FAILED e12c$i"
  CELL_HOLD= sh $E/run_cheap.sh $E/e12n$i $M novar || echo "FAILED e12n$i"
  CELL_HOLD=1 sh $E/run_cheap.sh $E/e12ch$i $M ctrl || echo "FAILED e12ch$i"
  CELL_HOLD=1 sh $E/run_cheap.sh $E/e12nh$i $M novar || echo "FAILED e12nh$i"
done
