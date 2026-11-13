s=$(date +%s.%N)
for i in 1 2 3; do r=$(python3 maze.py<m.txt); done
e=$(date +%s.%N)
[ "$r" = "$(cat exp.txt)" ] || { echo 0; exit; }
python3 -c "print(1/($e-$s))"
