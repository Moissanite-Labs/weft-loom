#!/bin/sh
python3 -c "
import subprocess,time,sys
s=time.time()
r=subprocess.run(['python3','sortints.py'],stdin=open('data.txt','rb'),stdout=open('out.txt','wb'),stderr=subprocess.DEVNULL)
e=time.time()
if r.returncode!=0: print(0); sys.exit(0)
if open('out.txt','rb').read()!=open('expected.txt','rb').read(): print(0); sys.exit(0)
print(1000/(e-s))
" 2>/dev/null
