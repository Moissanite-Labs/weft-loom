s=$(date +%s.%N)
o=$(python3 maze.py < maze.txt)
e=$(date +%s.%N)
[ "$o" = "$(cat expected.txt)" ] || { echo 0; exit; }
python3 -c "print(1/($e-$s))"
