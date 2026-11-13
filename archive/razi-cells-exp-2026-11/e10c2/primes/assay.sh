#!/bin/sh
cd "$(dirname "$0")"
r=$(python3 primes.py 5000000)
[ "$r" = "348513" ] || { echo 0; exit 1; }
python3 - <<'PY'
import subprocess,time,sys
t=time.perf_counter()
out=subprocess.run([sys.executable,"primes.py","200000000"],capture_output=True,text=True).stdout.strip()
dt=time.perf_counter()-t
if out!="11078937": print(0); sys.exit(1)
print(round(1000/dt,2))
PY
