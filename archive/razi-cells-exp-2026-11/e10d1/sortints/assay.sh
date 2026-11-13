#!/bin/sh
# prints ops/sec-ish score: 1e6 / elapsed seconds; 0 if output wrong
cd "$(dirname "$0")"
python3 - <<'EOF'
import subprocess, time, sys
best = None
for _ in range(3):
    t = time.perf_counter()
    r = subprocess.run(['python3', 'sortints.py'], stdin=open('data.txt','rb'), stdout=open('out.txt','wb'))
    e = time.perf_counter() - t
    if r.returncode != 0:
        print(0); sys.exit(0)
    best = e if best is None or e < best else best
if open('out.txt','rb').read() != open('expected.txt','rb').read():
    print(0); sys.exit(0)
print(round(1000.0 / best, 2))
EOF
