s=$(date +%s.%N)
o=$(python3 maze.py < big.txt)
e=$(date +%s.%N)
[ "$o" = "$(cat exp.txt)" ] && [ "$o" != "-1" ] && python3 -c "print(1/($e-$s))" || echo 0
