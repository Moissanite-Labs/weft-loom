#!/bin/sh
python3 - <<'EOF'
import subprocess, os, sys
exp = open("expected.txt", "rb").read()
times = []
for i in range(7):
    t0 = os.times()
    r = subprocess.run(["python3", "wf.py"], stdin=open("big.txt", "rb"), stdout=subprocess.PIPE)
    t1 = os.times()
    if r.returncode != 0 or r.stdout != exp:
        print(0); sys.exit(0)
    times.append((t1.children_user + t1.children_system) - (t0.children_user + t0.children_system))
times.sort()
print(round(100 / times[len(times)//2], 2))
EOF
