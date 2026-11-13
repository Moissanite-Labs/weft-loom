#!/bin/sh
# correctness checks then timing on a heavy workload
a=$(python3 primes.py 5000000); [ "$a" = "348513" ] || { echo 0; exit 0; }
b=$(python3 primes.py 100); [ "$b" = "25" ] || { echo 0; exit 0; }
c=$(python3 primes.py 2); [ "$c" = "0" ] || { echo 0; exit 0; }
python3 - <<'EOF'
import time, subprocess
t=time.perf_counter()
out=subprocess.run(["python3","primes.py","50000000"],capture_output=True,text=True).stdout.strip()
dt=time.perf_counter()-t
print(0 if out!="3001134" else round(1000/dt,2))
EOF
