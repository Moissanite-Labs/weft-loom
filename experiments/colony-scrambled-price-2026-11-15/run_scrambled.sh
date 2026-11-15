#!/bin/sh
# Scrambled-price control: three arms on the SP3 flat shape (4 kits, 400 energy each, born on mid).
#   T: price list shown, numbers true      S: price list shown, light and heavy numbers swapped
#   H: price list hidden (cost felt only)
# Sense is measured in every arm and shown in none, as in SP3 arms a and b.
# usage: run_scrambled.sh warm | run_scrambled.sh full     One run at a time, order fixed in PREREG.md.
cd $HOME/Work/razi-cells/exp
one() {  # arm run
  case $1 in
    T) P=1 X=0 ;; S) P=1 X=1 ;; H) P=0 X=0 ;;
  esac
  CELL_SENSE_DIR=$PWD/records CELL_PRICE_SHOW=$P CELL_PRICE_SCRAMBLE=$X CELL_SENSE_SHOW=0 sh run_metab.sh $2 > results/sc-$2.log 2>&1
  echo "$2 rc $?"
}
if [ "$1" = warm ]; then
  one T scwT; one S scwS; one H scwH   # warm the provider caches for all three prompt forms. Excluded.
else
  for i in 1 2 3 4; do for a in T S H; do one $a sc$a$i; done; done
fi
