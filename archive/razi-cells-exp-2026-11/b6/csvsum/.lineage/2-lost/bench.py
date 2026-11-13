import csv, io, os, subprocess, sys, time
from decimal import Decimal
N = 2000000
if not os.path.exists('input.csv'):
    totals = [0] * 200
    with open('input.csv', 'w') as f:
        f.write('id,cat,val\n')
        for i in range(N):
            c = (i * 37) % 200
            v = ((i * 7919) % 200001) - 100000
            totals[c] += v
            f.write(f'{i},cat{c:03d},{"-" if v < 0 else ""}{abs(v)//100}.{abs(v)%100:02d}\n')
    with open('expected.txt','w') as f:
        for c, v in enumerate(totals):
            f.write(f'cat{c:03d},{Decimal(v)/100:.2f}\n')
def check_small():
    cases = [
        'id,cat,val\n',
        'id,cat,val\n1,b,1.005\n2,a,-0.01\n3,b,0.005\n4,a,0.02\n',
        'id,cat,val\r\n1,"a,b",10.25\r\n2,"a""b",-2.50\r\n3,"two\nlines",1e2\r\n4,"a,b",-0.25\r\n',
        'id,cat,val\n1,x,999999999999999999.99\n2,x,.01\n3,y,-0.004\n4,z,+2\n5,z,3.14159\n',
    ]
    for text in cases:
        totals = {}
        for _, c, v in list(csv.reader(io.StringIO(text)))[1:]:
            totals[c] = totals.get(c, 0) + Decimal(v)
        out = io.StringIO()
        w = csv.writer(out, lineterminator='\n')
        for c in sorted(totals): w.writerow((c, format(totals[c], '.2f')))
        p = subprocess.run([sys.executable,'csvsum.py'],input=text.encode(),capture_output=True)
        if p.returncode or p.stdout != out.getvalue().encode(): return False
    return True
if not check_small():
    print(0); sys.exit(0)
t = time.perf_counter()
ok = True
for repeat in range(5):
    with open('input.csv','rb') as f:
        p = subprocess.run([sys.executable,'csvsum.py'],stdin=f,capture_output=True)
    with open('expected.txt','rb') as f:
        ok = ok and p.returncode == 0 and p.stdout == f.read()
elapsed = time.perf_counter()-t
with open('expected.txt','rb') as f: expected=f.read()
print(1/elapsed if ok else 0)
