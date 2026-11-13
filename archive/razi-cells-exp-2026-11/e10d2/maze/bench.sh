#!/bin/sh
# correctness on small cases + timed run on 2000x2000 maze (seed 1, p=0.28, expected 3998)
[ -f m1.txt ] || python3 gen.py 2000 1 0.28 > m1.txt
a=$(printf 'S.#\n.##\n..E\n' | python3 maze.py)
b=$(printf 'S#E\n' | python3 maze.py)
c=$(printf 'SE\n' | python3 maze.py)
d=$(printf 'S..\n###\n..E\n' | python3 maze.py)
[ "$a" = "4" ] && [ "$b" = "-1" ] && [ "$c" = "1" ] && [ "$d" = "-1" ] || { echo 0; exit 0; }
python3 - <<'EOF'
import subprocess, time
best=1e9; ok=True
for _ in range(3):
    t=time.perf_counter()
    out=subprocess.run(['python3','maze.py'],stdin=open('m1.txt','rb'),capture_output=True).stdout.strip()
    dt=time.perf_counter()-t
    best=min(best,dt); ok = ok and out==b'3998'
print(1000.0/best if ok else 0)
EOF
