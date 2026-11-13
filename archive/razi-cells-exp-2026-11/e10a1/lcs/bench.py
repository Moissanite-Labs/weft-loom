import json, subprocess, sys, time, importlib
cases=json.load(open("bench_cases.json"))
# end-to-end check through stdin/stdout
for a,b,exp in cases:
    out=subprocess.run([sys.executable,"lcs.py"],input=(a+"\n"+b+"\n").encode(),capture_output=True).stdout.decode().strip()
    if out!=str(exp):
        print(0); sys.exit(0)
import lcs
data=[(a.encode(),b.encode(),exp) for a,b,exp in cases]
REPS=120
best=None
for _ in range(3):
    t=time.perf_counter()
    ok=True
    for _ in range(REPS):
        for a,b,exp in data:
            if lcs.lcs(a,b)!=exp: ok=False
    dt=time.perf_counter()-t
    if not ok:
        print(0); sys.exit(0)
    best=dt if best is None or dt<best else best
print(round(REPS*len(data)/best,1))
