#!/bin/sh
# correctness checks first; print 0 on any failure
a=$(printf 'S.#\n.##\n..E\n' | python3 maze.py)
b=$(printf 'S#E\n' | python3 maze.py)
c=$(python3 gen.py 300 1 0.3 | python3 maze.py)
d=$(python3 gen.py 300 1 0.3 | python3 ref.py)
if [ "$a" != "4" ] || [ "$b" != "-1" ] || [ "$c" != "$d" ]; then echo 0; exit 0; fi
python3 - <<'EOF'
import subprocess, time
t0=time.time()
out=subprocess.run(['python3','maze.py'],stdin=open('t.txt','rb'),capture_output=True).stdout.decode().strip()
t1=time.time()
out2=subprocess.run(['python3','maze.py'],stdin=open('u.txt','rb'),capture_output=True).stdout.decode().strip()
t2=time.time()
if out!='-1' or out2!='-1': print(0)
else: print(round(1000.0/(t2-t0),2))
EOF
