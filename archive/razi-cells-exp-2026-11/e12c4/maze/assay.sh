s=$(date +%s.%N)
r=$(python3 maze.py < m.txt)
e=$(date +%s.%N)
[ "$r" = "$(cat exp.txt)" ] && echo "scale=3;1/($e-$s)" | bc || echo 0
