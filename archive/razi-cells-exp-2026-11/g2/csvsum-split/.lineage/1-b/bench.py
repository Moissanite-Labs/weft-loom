import subprocess, time, filecmp

cands = ['csvsum_base.py', 'cand1.py', 'cand2.py']
res = []
for c in cands:
    try:
        with open('data.csv','rb') as fin, open('/tmp/out.txt','wb') as fout:
            subprocess.run(['python3', c], stdin=fin, stdout=fout, stderr=subprocess.DEVNULL, timeout=20)
        ok = filecmp.cmp('expected.txt', '/tmp/out.txt', shallow=False)
    except Exception:
        ok = False
    if not ok:
        res.append((c, False, 0.0))
        continue
    t = time.time()
    with open('data.csv','rb') as fin:
        subprocess.run(['python3', c], stdin=fin, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    dt = time.time() - t
    res.append((c, ok, 1.0/dt))

for r in res:
    print(r)

best = max([r for r in res if r[1]], key=lambda x: x[2])
print('BEST', best)
with open(best[0],'rb') as a, open('csvsum.py','wb') as b:
    b.write(a.read())

with open('data.csv','rb') as fin, open('/tmp/final.txt','wb') as fout:
    subprocess.run(['python3','csvsum.py'], stdin=fin, stdout=fout)
print('FINAL_OK', filecmp.cmp('expected.txt','/tmp/final.txt', shallow=False))
