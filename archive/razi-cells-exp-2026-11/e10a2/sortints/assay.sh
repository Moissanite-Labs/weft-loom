#!/bin/sh
python3 - <<'P'
import subprocess,time,sys
exp=open('expected.txt','rb').read()
inp=open('data.txt','rb').read()
def run(b):
    return subprocess.run([sys.executable,'sortints.py'],input=b,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
# small edge tests: mixed whitespace, empty input, big ints, plus sign
if run(b'3 -1\n2\t-5  10\n')!=b'-5\n-1\n2\n3\n10\n' or run(b'')!=b'' or run(b'99999999999999999999 -7 +5\n')!=b'-7\n5\n99999999999999999999\n':
    print(0); sys.exit(0)
best=1e9
for _ in range(9):
    t=time.perf_counter(); out=run(inp); d=time.perf_counter()-t
    if out!=exp: print(0); sys.exit(0)
    best=min(best,d)
print(round(1/best,4))
P
