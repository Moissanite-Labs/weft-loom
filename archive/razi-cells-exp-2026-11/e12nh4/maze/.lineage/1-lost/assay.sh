[ "$(printf 'S.#\n.##\n..E\n' | python3 maze.py)" = 4 ] || { echo 0; exit; }
s=$(date +%s.%N); r=$(python3 maze.py < big.txt); e=$(date +%s.%N)
echo "$r" >&2
python3 -c "print(1/($e-$s))"
