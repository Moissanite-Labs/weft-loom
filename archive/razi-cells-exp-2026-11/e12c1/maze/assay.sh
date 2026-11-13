s=$(date +%s.%N); r=$(python3 maze.py < m.txt); e=$(date +%s.%N)
case "$r" in ''|*[!0-9-]*) echo 0;; *) python3 -c "print(1/($e-$s))";; esac
