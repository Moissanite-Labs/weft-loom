#!/bin/sh
# prints 1/best wall time (s) of csvsum.py over 8 runs on the 2M-row data.csv; 0 if output is wrong
python3 - <<'EOF'
import subprocess, time, sys
exp = open('expected.txt','rb').read()
best = None
for _ in range(8):
    with open('data.csv','rb') as f:
        t = time.perf_counter()
        p = subprocess.run([sys.executable, 'csvsum.py'], stdin=f, stdout=subprocess.PIPE)
        dt = time.perf_counter() - t
    if p.returncode != 0 or p.stdout != exp:
        print(0); sys.exit(0)
    best = dt if best is None or dt < best else best
print('%.4f' % (1.0/best))
EOF
