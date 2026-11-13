#!/bin/sh
# prints rows/sec * 1e-3 if output matches ref.txt, else 0
python3 - <<'EOF'
import subprocess, time, sys, os
if not os.path.exists("data.csv") or os.path.getsize("data.csv") < 40000000:
    subprocess.run([sys.executable,"gen.py","2000000"],stdout=open("data.csv","w"),check=True)
t=time.perf_counter()
p=subprocess.run([sys.executable,"csvsum.py"],stdin=open("data.csv","rb"),capture_output=True)
dt=time.perf_counter()-t
ref=open("ref.txt","rb").read()
if p.returncode!=0 or p.stdout!=ref:
    print(0); sys.exit(0)
print(round(2000000/dt/1000,1))
EOF
