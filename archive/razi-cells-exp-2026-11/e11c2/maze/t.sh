s=$(date +%s.%N)
r=$(python3 maze.py < m.txt)
e=$(date +%s.%N)
[ "$r" = "$(cat exp.txt)" ] || { echo 0; exit; }
python3 -c "print(10/($e-$s))"
