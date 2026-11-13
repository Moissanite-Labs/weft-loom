s=$(date +%s.%N)
o=$(python3 maze.py<m.txt)
e=$(date +%s.%N)
[ "$o" = "$(cat exp.txt)" ] && echo "1/($e-$s)" | bc -l || echo 0
