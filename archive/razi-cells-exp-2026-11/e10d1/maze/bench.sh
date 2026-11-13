#!/bin/sh
# correctness checks + timing; prints score = 1000/seconds, or 0 if wrong
export KMP_WARNINGS=0 OMP_NUM_THREADS=1
exec 2>/dev/null
a=$(printf 'S.#\n.##\n..E\n' | python3 maze.py)
b=$(printf 'S#E\n' | python3 maze.py)
c=$(printf 'SE\n' | python3 maze.py)
t=$(python3 maze.py < t.txt)
r=$(python3 ref.py < t.txt)
if [ "$a" != "4" ] || [ "$b" != "-1" ] || [ "$c" != "1" ] || [ "$t" != "$r" ]; then echo 0; exit 0; fi
s=$(python3 -c 'import time;print(time.time())')
x=$(python3 maze.py < m.txt)
y=$(python3 maze.py < m2.txt)
z=$(python3 maze.py < m3.txt)
e=$(python3 -c 'import time;print(time.time())')
if [ "$x" != "4002" ] || [ "$y" != "3998" ] || [ "$z" != "$(cat m3.ans)" ]; then echo 0; exit 0; fi
python3 -c "print(round(1000/($e-$s),2))"
