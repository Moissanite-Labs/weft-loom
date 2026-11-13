s=$(date +%s.%N)
o=$(python3 maze.py < big.txt)
e=$(date +%s.%N)
python3 -c "
o='$o'
print(0 if o in('-1','') else round(1/($e-$s),4))"
