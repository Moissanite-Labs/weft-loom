#!/bin/sh
# correctness checks, then timing; prints score = 1000/seconds (0 if wrong)
a=$(python3 primes.py 5000000 2>/dev/null); b=$(python3 primes.py 10 2>/dev/null); c=$(python3 primes.py 2 2>/dev/null); d=$(python3 primes.py 100 2>/dev/null)
if [ "$a" != "348513" ] || [ "$b" != "4" ] || [ "$c" != "0" ] || [ "$d" != "25" ]; then echo 0; exit 0; fi
python3 - 2>/dev/null <<'EOF'
import subprocess, time, sys
t=time.perf_counter()
for _ in range(3):
    out=subprocess.run([sys.executable,"primes.py","100000000"],capture_output=True,text=True).stdout.strip()
    if out!="5761455": print(0); sys.exit(0)
dt=time.perf_counter()-t
print(round(1000/dt,2))
EOF
