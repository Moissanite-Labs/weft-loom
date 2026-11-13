import subprocess, math

def run(inp):
    r = subprocess.run(['python3','csvsum.py'], input=inp, capture_output=True)
    return r.returncode, r.stdout.decode(), r.stderr.decode()

cases = []
# empty header only
cases.append((b'id,cat,val\n', '', 'header only'))
# basic
cases.append((b'id,cat,val\n1,a,1.5\n2,b,2.25\n3,a,2.5\n', 'a,4.00\nb,2.25\n', 'basic'))
# negatives and zeros
cases.append((b'id,cat,val\n1,z,-1.25\n2,a,0\n3,a,-0.75\n', 'a,-0.75\nz,-1.25\n', 'negatives'))
# rounding 2 decimals
cases.append((b'id,cat,val\n1,a,1.005\n2,a,1.005\n', 'a,2.01\n', 'round-half-even-ish? only check plausible'))
# many categories / integer vals
import random
random.seed(1)
lines=['id,cat,val']
sums={}
for i in range(1000):
    c='cat%03d'%(i%17)
    v=random.randint(-1000,1000)/100.0
    lines.append('%d,%s,%.2f'%(i,c,v))
    sums[c]=sums.get(c,0.0)+v
inp=('\n'.join(lines)+'\n').encode()
exp=''.join('%s,%.2f\n'%(k,sums[k]) for k in sorted(sums))
cases.append((inp, exp, 'random 1000'))

for inp, exp, name in cases:
    rc, out, err = run(inp)
    ok = (rc==0 and out==exp)
    print(('OK ' if ok else 'FAIL ')+name)
    if not ok:
        print(' rc',rc,'err',err[:200])
        print(' got',repr(out[:300]))
        print(' exp',repr(exp[:300]))
